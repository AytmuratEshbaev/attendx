"""Device endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


@pytest.mark.asyncio
async def test_create_device(client: AsyncClient) -> None:
    """Test POST /devices creates a device."""
    response = await client.post(
        "/api/v1/devices",
        json={
            "name": "New Terminal",
            "ip_address": "192.168.1.200",
            "port": 80,
            "username": "admin",
            "password": "testpass",
            "is_entry": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "New Terminal"
    assert data["data"]["ip_address"] == "192.168.1.200"


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, sample_device: Device) -> None:
    """Test GET /devices returns device list."""
    response = await client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_update_device(
    client: AsyncClient, sample_device: Device
) -> None:
    """Test PUT /devices/{id} updates a device."""
    response = await client.put(
        f"/api/v1/devices/{sample_device.id}",
        json={"name": "Updated Terminal"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Terminal"


@pytest.mark.asyncio
async def test_delete_device(
    client: AsyncClient, sample_device: Device
) -> None:
    """Test DELETE /devices/{id} soft-deletes device."""
    response = await client.delete(f"/api/v1/devices/{sample_device.id}")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Device deleted."


@pytest.mark.asyncio
async def test_device_health(
    client: AsyncClient, sample_device: Device
) -> None:
    """Test GET /devices/{id}/health returns health status."""
    response = await client.get(f"/api/v1/devices/{sample_device.id}/health")
    assert response.status_code == 200
    data = response.json()
    assert "is_online" in data["data"]
    assert "response_time_ms" in data["data"]


@pytest.mark.asyncio
async def test_sync_device(
    client: AsyncClient, sample_device: Device
) -> None:
    """Test POST /devices/{id}/sync returns queued status."""
    response = await client.post(f"/api/v1/devices/{sample_device.id}/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_crud_full_cycle(client: AsyncClient) -> None:
    """Test full device CRUD cycle."""
    # Create
    resp = await client.post(
        "/api/v1/devices",
        json={
            "name": "Cycle Terminal",
            "ip_address": "10.0.0.1",
            "password": "pass123",
        },
    )
    assert resp.status_code == 201
    device_id = resp.json()["data"]["id"]

    # Update
    resp = await client.put(
        f"/api/v1/devices/{device_id}",
        json={"name": "Updated Cycle"},
    )
    assert resp.status_code == 200

    # Health
    resp = await client.get(f"/api/v1/devices/{device_id}/health")
    assert resp.status_code == 200

    # Delete
    resp = await client.delete(f"/api/v1/devices/{device_id}")
    assert resp.status_code == 200
