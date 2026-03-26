"""Samsung SmartThings API client."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SmartThingsAPIError(Exception):
    """Base exception for SmartThings API errors."""
    pass


class RateLimitError(SmartThingsAPIError):
    """Raised when API rate limit is exceeded (429)."""
    pass


class InvalidRequestError(SmartThingsAPIError):
    """Raised when request is invalid (400)."""
    pass


class AuthenticationError(SmartThingsAPIError):
    """Raised when authentication fails (401/403)."""
    pass


class SmartThingsClient:
    """Async HTTP client for the Samsung SmartThings API.
    
    Creates a new client for each request to avoid "event loop closed" errors
    in test environments where event loops may be recreated.
    """

    # Rate limiting configuration
    RATE_LIMIT_DELAY = 0.5  # seconds between requests
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    _last_request_time: float = 0
    _request_lock = asyncio.Lock()

    def __init__(self) -> None:
        self.base_url = settings.smartthings_base_url.rstrip("/")
        self.token = settings.smartthings_token

    async def _create_client(self) -> httpx.AsyncClient:
        """Create a new HTTP client instance."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def _rate_limit(self) -> None:
        """Apply rate limiting to avoid 429 errors."""
        async with self._request_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
            self._last_request_time = time.time()

    async def _make_request(self, method: str, path: str, **kwargs) -> dict:
        """Make an HTTP request with retry logic and error handling."""
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()
                
                async with await self._create_client() as client:
                    if method == "GET":
                        resp = await client.get(path, **kwargs)
                    elif method == "POST":
                        resp = await client.post(path, **kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    # Handle specific HTTP status codes
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("Retry-After", self.RETRY_DELAY * (attempt + 1)))
                        logger.warning("Rate limited, waiting %d seconds before retry", retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    
                    resp.raise_for_status()
                    return resp.json() if resp.content else {}
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    raise InvalidRequestError(f"Invalid request: {e.request.url}") from e
                elif e.response.status_code in (401, 403):
                    raise AuthenticationError(f"Authentication failed: {e.response.status_code}") from e
                elif e.response.status_code == 429:
                    last_error = RateLimitError(f"Rate limit exceeded after {self.MAX_RETRIES} attempts")
                    continue
                else:
                    logger.error("HTTP error %s: %s", e.response.status_code, e)
                    raise SmartThingsAPIError(f"HTTP {e.response.status_code}: {e}") from e
            except httpx.RequestError as e:
                logger.error("Request error: %s", e)
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                raise SmartThingsAPIError(f"Request failed: {e}") from e
        
        # All retries exhausted
        if last_error:
            raise last_error
        raise SmartThingsAPIError("Request failed after all retries")

    # ---- Location / Room ----

    async def get_rooms(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        return await self._make_request("GET", f"/locations/{location_id}/rooms")

    # ---- Device ----

    async def get_devices(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        return await self._make_request("GET", "/devices", params={"locationId": location_id})

    async def get_device(self, device_id: str) -> dict:
        return await self._make_request("GET", f"/devices/{device_id}")

    async def get_device_status(self, device_id: str) -> dict:
        return await self._make_request("GET", f"/devices/{device_id}/status")

    async def get_device_health(self, device_id: str) -> dict:
        return await self._make_request("GET", f"/devices/{device_id}/health")

    async def get_device_capabilities(self, device_id: str) -> dict:
        """Get device capabilities from the device info endpoint.
        
        Note: The dedicated /capabilities endpoint may return 406/401 errors.
        We extract capabilities from the main device info response instead.
        """
        try:
            # Get full device info which includes capabilities in components
            device_data = await self.get_device(device_id)
            
            # Extract and restructure capabilities for easier consumption
            result = {
                "deviceId": device_id,
                "label": device_data.get("label", ""),
                "model": device_data.get("model", ""),
                "manufacturerName": device_data.get("manufacturerName", ""),
                "components": []
            }
            
            for comp in device_data.get("components", []):
                comp_info = {
                    "id": comp.get("id"),
                    "label": comp.get("label", ""),
                    "capabilities": [
                        {"id": cap.get("id"), "version": cap.get("version", "")}
                        for cap in comp.get("capabilities", [])
                    ]
                }
                result["components"].append(comp_info)
            
            return result
        except Exception as e:
            logger.error("Failed to get capabilities for %s: %s", device_id, e)
            raise


# Module-level singleton
smartthings = SmartThingsClient()
