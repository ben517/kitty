"""Samsung SmartThings API client."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SmartThingsClient:
    """Async HTTP client for the Samsung SmartThings API.
    
    Creates a new client for each request to avoid "event loop closed" errors
    in test environments where event loops may be recreated.
    """

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

    # ---- Location / Room ----

    async def get_rooms(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        async with await self._create_client() as client:
            resp = await client.get(f"/locations/{location_id}/rooms")
            resp.raise_for_status()
            return resp.json()

    # ---- Device ----

    async def get_devices(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        async with await self._create_client() as client:
            resp = await client.get("/devices", params={"locationId": location_id})
            resp.raise_for_status()
            return resp.json()

    async def get_device(self, device_id: str) -> dict:
        async with await self._create_client() as client:
            resp = await client.get(f"/devices/{device_id}")
            resp.raise_for_status()
            return resp.json()

    async def get_device_status(self, device_id: str) -> dict:
        async with await self._create_client() as client:
            resp = await client.get(f"/devices/{device_id}/status")
            resp.raise_for_status()
            return resp.json()

    async def get_device_health(self, device_id: str) -> dict:
        async with await self._create_client() as client:
            resp = await client.get(f"/devices/{device_id}/health")
            resp.raise_for_status()
            return resp.json()

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
