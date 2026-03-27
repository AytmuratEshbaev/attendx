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
    user = User(
        id=uuid.uuid4(),
        username="logintest",
        password_hash=hash_password("Secret123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest", "password": "Secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient) -> None:
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
async def test_login_inactive_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test login with inactive account returns 401."""
    user = User(
        id=uuid.uuid4(),
        username="inactive_user",
        password_hash=hash_password("Secret123"),
        role="admin",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactive_user", "password": "Secret123"},
    )
    assert response.status_code == 401


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
    from app.core.dependencies import get_current_active_user
    from app.main import app

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
        password_hash=hash_password("Secret123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "refreshtest", "password": "Secret123"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_change_password(
    client: AsyncClient, db_session: AsyncSession, sample_user: User
) -> None:
    """Test POST /auth/change-password succeeds."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "testpass123", "new_password": "NewPass1234"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_old(client: AsyncClient) -> None:
    """Test change password with wrong old password returns 401."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "wrongold123", "new_password": "NewPass1234"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_weak_new(client: AsyncClient) -> None:
    """Test change password with weak new password returns 422."""
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "testpass123", "new_password": "weak"},
    )
    assert response.status_code == 422
