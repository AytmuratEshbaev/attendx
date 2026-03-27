"""Authentication endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_login_valid(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test login with valid credentials returns tokens."""
    # Create a user with known password
    user = User(
        id=uuid.uuid4(),
        username="logintest",
        password_hash=hash_password("secret123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient) -> None:
    """Test login with invalid credentials returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "wrongpass"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_short_password(client: AsyncClient) -> None:
    """Test login with too short password returns 422."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "abc", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_me_with_token(
    client: AsyncClient, sample_user: User, auth_headers: dict
) -> None:
    """Test /auth/me with valid token returns user info."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == sample_user.username


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    """Test /auth/me without token returns 401."""
    # Override the dependency back to the real one for this test
    from app.core.dependencies import get_current_active_user
    from app.main import app

    # Remove the override so real auth is used
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /auth/refresh returns new tokens."""
    user = User(
        id=uuid.uuid4(),
        username="refreshtest",
        password_hash=hash_password("secret123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login first
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "refreshtest", "password": "secret123"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    # Now refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
