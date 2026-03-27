"""External API (API key auth) endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_api_key, get_db
from app.models.api_key import APIKey


@pytest.mark.asyncio
async def test_external_students_with_api_key(
    db_session: AsyncSession,
) -> None:
    """Test GET /external/students with valid API key."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    async def _override_get_api_key():
        return APIKey(name="test-key", key_hash="", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_api_key] = _override_get_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/external/students")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_external_today_with_api_key(
    db_session: AsyncSession,
) -> None:
    """Test GET /external/attendance/today with valid API key."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    async def _override_get_api_key():
        return APIKey(name="test-key", key_hash="", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_api_key] = _override_get_api_key

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/external/attendance/today")
        assert response.status_code == 200

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_external_without_api_key(
    db_session: AsyncSession,
) -> None:
    """Test external endpoint without API key returns 401."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    # Only override DB, not the API key dependency
    app.dependency_overrides[get_db] = _override_get_db
    # Make sure API key dependency is NOT overridden
    if get_api_key in app.dependency_overrides:
        del app.dependency_overrides[get_api_key]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/external/students")
        assert response.status_code == 401

    app.dependency_overrides.clear()
