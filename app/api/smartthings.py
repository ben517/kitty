"""Samsung SmartThings API client."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SmartThingsClient:
    """Async HTTP client for the Samsung SmartThings API."""

    def __init__(self) -> None:
        self.base_url = settings.smartthings_base_url.rstrip("/")
        self.token = settings.smartthings_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ---- Location / Room ----

    async def get_rooms(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        client = await self._ensure_client()
        resp = await client.get(f"/locations/{location_id}/rooms")
        resp.raise_for_status()
        return resp.json()

    # ---- Device ----

    async def get_devices(self, location_id: Optional[str] = None) -> dict:
        location_id = location_id or settings.smartthings_location_id
        client = await self._ensure_client()
        resp = await client.get("/devices", params={"locationId": location_id})
        resp.raise_for_status()
        return resp.json()

    async def get_device(self, device_id: str) -> dict:
        client = await self._ensure_client()
        resp = await client.get(f"/devices/{device_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_device_status(self, device_id: str) -> dict:
        client = await self._ensure_client()
        resp = await client.get(f"/devices/{device_id}/status")
        resp.raise_for_status()
        return resp.json()

    async def get_device_health(self, device_id: str) -> dict:
        client = await self._ensure_client()
        resp = await client.get(f"/devices/{device_id}/health")
        resp.raise_for_status()
        return resp.json()

    async def get_device_capabilities(self, device_id: str) -> dict:
        client = await self._ensure_client()
        resp = await client.get(f"/devices/{device_id}/capabilities")
        resp.raise_for_status()
        return resp.json()

    async def query_capabilities(self, queries: list[dict]) -> dict:
        client = await self._ensure_client()
        resp = await client.post("/capabilities/query", json={"query": queries})
        resp.raise_for_status()
        return resp.json()


# Module-level singleton
smartthings = SmartThingsClient()
