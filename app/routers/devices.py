"""Device router – proxy device queries to SmartThings API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.api.smartthings import smartthings

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices(location_id: Optional[str] = Query(None)):
    return await smartthings.get_devices(location_id)


@router.get("/{device_id}")
async def get_device(device_id: str):
    return await smartthings.get_device(device_id)


@router.get("/{device_id}/status")
async def get_device_status(device_id: str):
    return await smartthings.get_device_status(device_id)


@router.get("/{device_id}/health")
async def get_device_health(device_id: str):
    return await smartthings.get_device_health(device_id)


@router.get("/{device_id}/capabilities")
async def get_device_capabilities(device_id: str):
    return await smartthings.get_device_capabilities(device_id)
