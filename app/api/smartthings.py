"""Samsung SmartThings API client."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class _TimedCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any:
        """Get value from cache if not expired."""
        async with self._lock:
            if key not in self._cache:
                logger.info("[Cache] MISS: key=%s", key)
                return None
            value, expire_time = self._cache[key]
            if time.time() > expire_time:
                del self._cache[key]
                logger.info("[Cache] EXPIRED: key=%s", key)
                return None
            logger.info("[Cache] HIT: key=%s", key)
            return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL (seconds)."""
        async with self._lock:
            expire_time = time.time() + ttl
            self._cache[key] = (value, expire_time)
            logger.info("[Cache] SET: key=%s, ttl=%ds", key, ttl)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info("[Cache] DELETE: key=%s", key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info("[Cache] CLEAR: cleared=%d entries", count)


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

    # Cache TTL configuration (seconds)
    CACHE_TTL_DEVICES = 60  # Device list cache for 60 seconds
    CACHE_TTL_DEVICE = 30   # Single device info cache for 30 seconds
    # Device status cache for 10 seconds (changes frequently)
    CACHE_TTL_STATUS = 10
    CACHE_TTL_HEALTH = 30   # Device health cache for 30 seconds
    CACHE_TTL_ROOMS = 300   # Room list cache for 5 minutes (rarely changes)

    _last_request_time: float = 0
    _request_lock = asyncio.Lock()

    def __init__(self) -> None:
        self.base_url = settings.smartthings_base_url.rstrip("/")
        self.token = settings.smartthings_token
        self._cache = _TimedCache()

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

    def _make_cache_key(self, method: str, path: str, **kwargs) -> str:
        """Generate a unique cache key for the request."""
        # Include relevant kwargs in cache key (params matter for GET requests)
        params = kwargs.get("params", {})
        params_str = ""
        if params:
            sorted_params = sorted(params.items())
            params_str = "?" + "&".join(f"{k}={v}" for k, v in sorted_params)
        return f"{method}:{path}{params_str}"

    async def _make_request(
        self,
        method: str,
        path: str,
        use_cache: bool = True,
        cache_ttl: int = 0,
        **kwargs
    ) -> dict:
        """Make an HTTP request with retry logic, error handling, and caching.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            use_cache: Whether to use cache for this request
            cache_ttl: Cache TTL in seconds (0 means no caching)
            **kwargs: Additional arguments for httpx
        """
        cache_key = self._make_cache_key(method, path, **kwargs)

        # Try to get from cache first
        if use_cache and method == "GET" and cache_ttl > 0:
            cached_value = await self._cache.get(cache_key)
            if cached_value is not None:
                return cached_value

        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()
                logger.info(
                    "[SmartThings API] REQUEST: method=%s, path=%s, "
                    "attempt=%d/%d",
                    method, path, attempt + 1, self.MAX_RETRIES
                )

                async with await self._create_client() as client:
                    if method == "GET":
                        resp = await client.get(path, **kwargs)
                    elif method == "POST":
                        resp = await client.post(path, **kwargs)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    # Handle specific HTTP status codes
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get(
                            "Retry-After", self.RETRY_DELAY * (attempt + 1)
                        ))
                        logger.warning(
                            "Rate limited, waiting %d seconds before retry",
                            retry_after
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    result = resp.json() if resp.content else {}
                    logger.info(
                        "[SmartThings API] RESPONSE: method=%s, path=%s, "
                        "status=%d",
                        method, path, resp.status_code
                    )

                    # Store in cache if enabled
                    if use_cache and method == "GET" and cache_ttl > 0:
                        await self._cache.set(cache_key, result, cache_ttl)

                    return result

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    raise InvalidRequestError(
                        f"Invalid request: {e.request.url}"
                    ) from e
                elif e.response.status_code in (401, 403):
                    raise AuthenticationError(
                        f"Authentication failed: {e.response.status_code}"
                    ) from e
                elif e.response.status_code == 429:
                    last_error = RateLimitError(
                        "Rate limit exceeded after "
                        f"{self.MAX_RETRIES} attempts"
                    )
                    continue
                else:
                    code = e.response.status_code
                    logger.error("HTTP error %s: %s", code, e)
                    raise SmartThingsAPIError(
                        f"HTTP {code}: {e}"
                    ) from e
            except httpx.RequestError as e:
                logger.error("Request error: %s", e)
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                raise SmartThingsAPIError(
                    f"Request failed: {e}"
                ) from e

        # All retries exhausted
        if last_error:
            raise last_error
        raise SmartThingsAPIError("Request failed after all retries")

    # ---- Location / Room ----

    async def get_rooms(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        return await self._make_request(
            "GET",
            f"/locations/{location_id}/rooms",
            use_cache=True,
            cache_ttl=self.CACHE_TTL_ROOMS
        )

    # ---- Device ----

    async def get_devices(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        return await self._make_request(
            "GET",
            "/devices",
            params={"locationId": location_id},
            use_cache=True,
            cache_ttl=self.CACHE_TTL_DEVICES
        )

    async def get_device(self, device_id: str) -> dict:
        return await self._make_request(
            "GET",
            f"/devices/{device_id}",
            use_cache=True,
            cache_ttl=self.CACHE_TTL_DEVICE
        )

    async def get_device_status(self, device_id: str) -> dict:
        return await self._make_request(
            "GET",
            f"/devices/{device_id}/status",
            use_cache=True,
            cache_ttl=self.CACHE_TTL_STATUS
        )

    async def get_device_health(self, device_id: str) -> dict:
        return await self._make_request(
            "GET",
            f"/devices/{device_id}/health",
            use_cache=True,
            cache_ttl=self.CACHE_TTL_HEALTH
        )

    async def clear_cache(self) -> None:
        """Clear all cached data."""
        logger.info("[SmartThings API] CLEAR_CACHE triggered")
        await self._cache.clear()
        logger.info("[SmartThings API] CLEAR_CACHE completed")

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        logger.info("[SmartThings API] Client closing")
        await self._cache.clear()
        logger.info("[SmartThings API] Client closed")

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
                        {
                            "id": cap.get("id"),
                            "version": cap.get("version", "")
                        }
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
