"""Security administration dashboard endpoints (super_admin only)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis, require_role
from app.models.user import User
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/blocked-ips", response_model=SuccessResponse[list])
async def list_blocked(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    redis=Depends(get_redis),
) -> SuccessResponse[list]:
    """List all currently blocked IPs and usernames."""
    from app.core.rate_limiter import BruteForceProtection

    brute = BruteForceProtection(redis)
    blocked = await brute.get_blocked_identifiers()
    return SuccessResponse(data=blocked)


@router.post("/unblock/{identifier}", response_model=SuccessResponse[dict])
async def unblock_identifier(
    identifier: str,
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    redis=Depends(get_redis),
) -> SuccessResponse[dict]:
    """Manually unblock an IP or username."""
    await redis.delete(f"bruteforce:login:{identifier}")
    return SuccessResponse(data={"message": f"Unblocked: {identifier}"})


@router.get("/api-keys", response_model=SuccessResponse[list])
async def security_api_keys(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list]:
    """List all API keys with usage stats."""
    from app.core.api_key_manager import APIKeyManager

    manager = APIKeyManager(db)
    keys = await manager.list_keys()
    return SuccessResponse(data=keys)


@router.get("/audit-logs", response_model=SuccessResponse[dict])
async def security_audit_logs(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[dict]:
    """Shortcut to recent audit logs (last 20 entries)."""
    from app.services.audit_service import AuditService

    svc = AuditService(db)
    logs, total = await svc.get_logs(limit=20)
    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
    return SuccessResponse(data={"items": items, "total": total})


@router.post("/revoke-all-sessions", response_model=SuccessResponse[dict])
async def revoke_all_sessions(
    current_user: Annotated[User, Depends(require_role("super_admin"))],
    redis=Depends(get_redis),
) -> SuccessResponse[dict]:
    """
    Revoke all active JWT sessions by setting a global revocation timestamp.

    Any token issued before this timestamp will be rejected.
    """
    import time

    ts = str(time.time())
    await redis.set("auth:global_revocation_ts", ts)
    return SuccessResponse(
        data={
            "message": "All sessions revoked",
            "revocation_timestamp": ts,
            "revoked_by": str(current_user.id),
        }
    )


@router.get("/backup-status", response_model=SuccessResponse[dict])
async def backup_status(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    redis=Depends(get_redis),
) -> SuccessResponse[dict]:
    """Return information about the last completed backup."""
    last_backup = await redis.get("backup:last_completed")
    last_error = await redis.get("backup:last_error")
    return SuccessResponse(
        data={
            "last_completed": last_backup,
            "last_error": last_error,
        }
    )


@router.post("/backup-now", response_model=SuccessResponse[dict])
async def trigger_backup(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    redis=Depends(get_redis),
) -> SuccessResponse[dict]:
    """
    Trigger a manual database backup in the background.

    Runs as a fire-and-forget asyncio task.
    """
    import asyncio

    async def _run_backup() -> None:
        import json
        import time

        try:
            from scripts.backup import BackupManager

            mgr = BackupManager()
            results = mgr.run_full_backup()
            await redis.set("backup:last_completed", json.dumps(results))
        except Exception as exc:
            await redis.set("backup:last_error", str(exc))

    asyncio.create_task(_run_backup())
    return SuccessResponse(data={"message": "Backup started in background"})
