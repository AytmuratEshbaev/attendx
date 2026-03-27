"""Webhook endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook


@pytest.mark.asyncio
async def test_create_webhook(client: AsyncClient) -> None:
    """Test POST /webhooks creates a webhook."""
    response = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://example.com/webhook",
            "events": ["attendance.entry", "attendance.exit"],
            "description": "Test webhook",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["url"] == "https://example.com/webhook"


@pytest.mark.asyncio
async def test_create_webhook_auto_secret(client: AsyncClient) -> None:
    """Test webhook secret is auto-generated when not provided."""
    response = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://example.com/hook",
            "events": ["attendance.entry"],
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_create_webhook_invalid_event(client: AsyncClient) -> None:
    """Test creating webhook with invalid event type returns 422."""
    response = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://example.com/hook",
            "events": ["invalid.event"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_webhook_invalid_url(client: AsyncClient) -> None:
    """Test creating webhook with invalid URL returns 422."""
    response = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "ftp://example.com/hook",
            "events": ["attendance.entry"],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_webhooks(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test GET /webhooks returns list."""
    webhook = Webhook(
        url="https://test.com/wh",
        secret="test-secret",
        events=["attendance.entry"],
    )
    db_session.add(webhook)
    await db_session.commit()

    response = await client.get("/api/v1/webhooks")
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_update_webhook(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test PUT /webhooks/{id} updates webhook."""
    webhook = Webhook(
        url="https://test.com/wh",
        secret="test-secret",
        events=["attendance.entry"],
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)

    response = await client.put(
        f"/api/v1/webhooks/{webhook.id}",
        json={"description": "Updated desc"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_delete_webhook(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test DELETE /webhooks/{id} deletes webhook."""
    webhook = Webhook(
        url="https://test.com/wh",
        secret="test-secret",
        events=["attendance.entry"],
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)

    response = await client.delete(f"/api/v1/webhooks/{webhook.id}")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Webhook deleted."


@pytest.mark.asyncio
async def test_webhook_logs(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /webhooks/{id}/logs returns paginated logs."""
    webhook = Webhook(
        url="https://test.com/wh",
        secret="test-secret",
        events=["attendance.entry"],
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)

    response = await client.get(f"/api/v1/webhooks/{webhook.id}/logs")
    assert response.status_code == 200
    assert "pagination" in response.json()


@pytest.mark.asyncio
async def test_crud_full_cycle(client: AsyncClient) -> None:
    """Test full webhook CRUD cycle."""
    # Create
    resp = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "https://cycle.com/hook",
            "events": ["attendance.entry"],
        },
    )
    assert resp.status_code == 201
    wh_id = resp.json()["data"]["id"]

    # List
    resp = await client.get("/api/v1/webhooks")
    assert resp.status_code == 200

    # Update
    resp = await client.put(
        f"/api/v1/webhooks/{wh_id}",
        json={"description": "Cycle test"},
    )
    assert resp.status_code == 200

    # Logs
    resp = await client.get(f"/api/v1/webhooks/{wh_id}/logs")
    assert resp.status_code == 200

    # Delete
    resp = await client.delete(f"/api/v1/webhooks/{wh_id}")
    assert resp.status_code == 200
