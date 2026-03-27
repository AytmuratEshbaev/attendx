"""User management endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users_returns_paginated(client: AsyncClient) -> None:
    """Admin can list users."""
    resp = await client.get("/api/v1/users")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data


@pytest.mark.asyncio
async def test_list_users_filter_by_role(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Filter by role returns only matching users."""
    teacher = User(
        id=uuid.uuid4(),
        username="filter_teacher",
        password_hash=hash_password("pass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(teacher)
    await db_session.commit()

    resp = await client.get("/api/v1/users?role=teacher")
    assert resp.status_code == 200
    roles = [u["role"] for u in resp.json()["data"]]
    assert all(r == "teacher" for r in roles)


@pytest.mark.asyncio
async def test_list_users_forbidden_for_teacher(teacher_client: AsyncClient) -> None:
    """Teacher cannot access user management."""
    resp = await teacher_client.get("/api/v1/users")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient) -> None:
    """Admin can create a new user."""
    resp = await client.post(
        "/api/v1/users",
        json={
            "username": "newuser_test",
            "password": "password123",
            "role": "teacher",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["username"] == "newuser_test"
    assert data["data"]["role"] == "teacher"


@pytest.mark.asyncio
async def test_create_user_duplicate_username(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Creating a user with duplicate username returns 409."""
    user = User(
        id=uuid.uuid4(),
        username="duplicate_user",
        password_hash=hash_password("pass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/users",
        json={
            "username": "duplicate_user",
            "password": "password123",
            "role": "teacher",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_user_invalid_role(client: AsyncClient) -> None:
    """Creating a user with invalid role returns 422."""
    resp = await client.post(
        "/api/v1/users",
        json={
            "username": "badrole_user",
            "password": "password123",
            "role": "student",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_forbidden_for_teacher(teacher_client: AsyncClient) -> None:
    """Teacher cannot create users."""
    resp = await teacher_client.post(
        "/api/v1/users",
        json={"username": "sneaky", "password": "password123", "role": "teacher"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_email(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin can update a user's email."""
    user = User(
        id=uuid.uuid4(),
        username="update_email_user",
        password_hash=hash_password("pass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/users/{user.id}",
        json={"email": "updated@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_deactivate(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin can deactivate a user."""
    user = User(
        id=uuid.uuid4(),
        username="deactivate_user",
        password_hash=hash_password("pass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/users/{user.id}",
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient) -> None:
    """Updating a non-existent user returns 404."""
    resp = await client.put(
        f"/api/v1/users/{uuid.uuid4()}",
        json={"email": "ghost@example.com"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_user_prevent_demote_last_super_admin(
    client: AsyncClient, sample_user: User
) -> None:
    """Cannot demote the only super_admin."""
    resp = await client.put(
        f"/api/v1/users/{sample_user.id}",
        json={"role": "admin"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_user_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin can delete a regular user."""
    user = User(
        id=uuid.uuid4(),
        username="delete_me_user",
        password_hash=hash_password("pass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/users/{user.id}")
    assert resp.status_code == 200
    assert "deleted" in resp.json()["data"]["message"].lower()


@pytest.mark.asyncio
async def test_delete_super_admin_rejected(
    client: AsyncClient, sample_user: User
) -> None:
    """Cannot delete a super_admin account."""
    resp = await client.delete(f"/api/v1/users/{sample_user.id}")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_self_rejected(
    client: AsyncClient, sample_user: User
) -> None:
    """Cannot delete your own account (sample_user is the authenticated user)."""
    resp = await client.delete(f"/api/v1/users/{sample_user.id}")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient) -> None:
    """Deleting a non-existent user returns 404."""
    resp = await client.delete(f"/api/v1/users/{uuid.uuid4()}")
    assert resp.status_code == 404
