"""FastAPI dependency injection functions."""

import uuid
from collections.abc import AsyncIterator, Callable
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header, Request
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from app.core.permissions import has_permission
from app.core.redis import get_redis as _get_redis
from app.core.redis import is_token_blacklisted
from app.core.security import verify_api_key, verify_token
from app.models.api_key import APIKey
from app.models.user import User


# -- Database ------------------------------------------------------------------


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# -- Redis ---------------------------------------------------------------------


async def get_redis() -> aioredis.Redis:
    """Return the Redis connection."""
    return await _get_redis()


# -- Auth: Current User --------------------------------------------------------


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract JWT from Authorization header, validate, return User."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationException("Missing or invalid Authorization header.")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_token(token)
    except JWTError:
        raise AuthenticationException("Invalid or expired token.")

    if payload.get("type") != "access":
        raise AuthenticationException("Invalid token type.")

    # Check blacklist (skip gracefully if Redis is unavailable)
    jti = payload.get("jti")
    if jti:
        try:
            if await is_token_blacklisted(jti):
                raise AuthenticationException("Token has been revoked.")
        except RuntimeError:
            pass  # Redis not initialized — skip blacklist check

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid token payload.")

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise AuthenticationException("Invalid user id in token.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthenticationException("User not found.")

    # Store token payload on request for logout
    request.state.token_payload = payload
    return user


# -- Auth: Active User ---------------------------------------------------------


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the current user is active."""
    if not user.is_active:
        raise AuthorizationException("User account is deactivated.")
    return user


# -- Auth: Role Check with Hierarchy -------------------------------------------


def require_role(min_role: str) -> Callable:
    """Dependency factory that checks user role using hierarchy.

    Usage: Depends(require_role("admin"))
    A super_admin can access admin endpoints, etc.
    """

    async def _check_role(
        user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if not has_permission(user.role, min_role):
            raise AuthorizationException(
                f"Role '{user.role}' does not have sufficient permissions. "
                f"Required: {min_role} or higher."
            )
        return user

    return _check_role


# -- API Key Auth --------------------------------------------------------------


async def get_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: str = Header(alias="X-API-Key", default=""),
) -> APIKey:
    """Validate the X-API-Key header against stored keys."""
    if not x_api_key:
        raise AuthenticationException("Missing API key.")

    # Check against default API key first
    if x_api_key == settings.DEFAULT_API_KEY:
        return APIKey(name="default", key_hash="", is_active=True)

    # Check database
    result = await db.execute(select(APIKey).where(APIKey.is_active.is_(True)))
    keys = result.scalars().all()
    for key in keys:
        if verify_api_key(x_api_key, key.key_hash):
            return key

    raise AuthenticationException("Invalid API key.")
