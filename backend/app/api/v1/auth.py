"""Authentication endpoints."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.core.error_codes import ErrorCode
from app.core.exceptions import AuthenticationException
from app.core.rate_limiter import BruteForceProtection
from app.core.redis import blacklist_token, is_token_blacklisted
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
import structlog

from app.schemas.common import SuccessResponse
from app.services.audit_service import AuditService

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


async def extract_token(
    authorization: str = Header(..., alias="Authorization"),
) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise AuthenticationException(
            "Invalid authorization header",
            error_code=ErrorCode.TOKEN_INVALID,
        )
    return authorization[7:]


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user and return JWT tokens."""
    try:
        redis = await get_redis()
        bf = BruteForceProtection(redis)
        status = await bf.check_login_attempt(body.username)
        if not status["allowed"]:
            raise AuthenticationException(
                "Account temporarily locked due to too many failed attempts. "
                f"Try again in {status['locked_until']}.",
                error_code=ErrorCode.ACCOUNT_LOCKED,
            )
    except RuntimeError:
        pass  # Redis not available, skip brute force check

    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        try:
            redis = await get_redis()
            await BruteForceProtection(redis).record_failed_attempt(body.username)
        except RuntimeError:
            logger.debug("brute_force_redis_unavailable")
        raise AuthenticationException(
            "Invalid username or password.",
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )

    if not user.is_active:
        raise AuthenticationException(
            "Account is deactivated.",
            error_code=ErrorCode.ACCOUNT_INACTIVE,
        )

    try:
        redis = await get_redis()
        await BruteForceProtection(redis).record_successful_login(body.username)
    except RuntimeError:
        logger.debug("brute_force_redis_unavailable")

    jti = str(uuid.uuid4())
    token_data = {"sub": str(user.id), "role": user.role, "jti": jti}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    client_ip = request.client.host if request.client else None
    await AuditService(db).log(user.id, "login", "user", str(user.id), ip_address=client_ip)

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_EXPIRY_MINUTES * 60,
        )
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh an access token using a refresh token."""
    try:
        payload = verify_token(body.refresh_token)
    except Exception:
        raise AuthenticationException(
            "Invalid refresh token.",
            error_code=ErrorCode.TOKEN_INVALID,
        )

    if payload.get("type") != "refresh":
        raise AuthenticationException(
            "Invalid token type.",
            error_code=ErrorCode.TOKEN_INVALID,
        )

    jti = payload.get("jti")
    if jti:
        try:
            if await is_token_blacklisted(jti):
                raise AuthenticationException(
                    "Token has been revoked.",
                    error_code=ErrorCode.TOKEN_INVALID,
                )
        except RuntimeError:
            logger.debug("token_blacklist_redis_unavailable")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException(
            "Invalid token payload.",
            error_code=ErrorCode.TOKEN_INVALID,
        )
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationException(
            "Invalid user id in token.",
            error_code=ErrorCode.TOKEN_INVALID,
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthenticationException(
            "User not found or inactive.",
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )

    new_jti = str(uuid.uuid4())
    token_data = {"sub": str(user.id), "role": user.role, "jti": new_jti}
    access_token = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    return SuccessResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=settings.JWT_ACCESS_EXPIRY_MINUTES * 60,
        )
    )


@router.post("/logout", response_model=SuccessResponse[dict])
async def logout(
    request: Request,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Blacklist the current token via its jti claim."""
    token_payload = getattr(request.state, "token_payload", {})
    jti = token_payload.get("jti")
    if jti:
        ttl = settings.JWT_ACCESS_EXPIRY_MINUTES * 60
        await blacklist_token(jti, ttl)

    await AuditService(db).log(user.id, "logout", "user", str(user.id))

    return SuccessResponse(data={"message": "Successfully logged out"})


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def me(
    user: Annotated[User, Depends(get_current_active_user)],
):
    """Return the current authenticated user."""
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.post("/change-password", response_model=SuccessResponse[dict])
async def change_password(
    body: ChangePasswordRequest,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change the current user's password."""
    if not verify_password(body.old_password, user.password_hash):
        raise AuthenticationException(
            "Current password is incorrect.",
            error_code=ErrorCode.INVALID_CREDENTIALS,
        )

    user.password_hash = hash_password(body.new_password)
    await db.flush()

    await AuditService(db).log(user.id, "change_password", "user", str(user.id))

    return SuccessResponse(data={"message": "Password changed successfully"})
