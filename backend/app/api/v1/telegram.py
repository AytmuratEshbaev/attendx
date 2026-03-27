"""Telegram bot subscription management endpoints."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db, require_role
from app.core.exceptions import AttendXException
from app.models.student import Student
from app.models.telegram_sub import TelegramSub
from app.models.user import User
from app.schemas.common import SuccessResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/stats", response_model=SuccessResponse[dict])
async def telegram_stats(
    _user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get Telegram bot subscription statistics (admin only)."""
    total_subs = (
        await db.execute(select(func.count(TelegramSub.id)))
    ).scalar() or 0

    active_subs = (
        await db.execute(
            select(func.count(TelegramSub.id)).where(
                TelegramSub.is_active.is_(True)
            )
        )
    ).scalar() or 0

    unique_parents = (
        await db.execute(
            select(func.count(func.distinct(TelegramSub.chat_id))).where(
                TelegramSub.is_active.is_(True)
            )
        )
    ).scalar() or 0

    # Students with at least one active telegram subscription
    students_with_sub = (
        await db.execute(
            select(func.count(func.distinct(TelegramSub.student_id))).where(
                TelegramSub.is_active.is_(True),
                TelegramSub.student_id.isnot(None),
            )
        )
    ).scalar() or 0

    total_students = (
        await db.execute(
            select(func.count(Student.id)).where(Student.is_active.is_(True))
        )
    ).scalar() or 0

    coverage_pct = round(students_with_sub / total_students * 100) if total_students else 0

    # Recent subscriptions (last 10)
    recent_result = await db.execute(
        select(TelegramSub, Student)
        .outerjoin(Student, TelegramSub.student_id == Student.id)
        .where(TelegramSub.is_active.is_(True))
        .order_by(TelegramSub.created_at.desc())
        .limit(10)
    )
    recent = []
    for sub, student in recent_result:
        recent.append({
            "chat_id": sub.chat_id,
            "phone": sub.phone[-4:].rjust(12, "*"),  # mask phone
            "student_name": student.name if student else "—",
            "class_name": student.class_name if student else "—",
            "subscribed_at": sub.created_at.isoformat(),
        })

    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", None)

    return SuccessResponse(
        data={
            "bot_username": bot_username,
            "bot_configured": bool(getattr(settings, "TELEGRAM_BOT_TOKEN", None)),
            "total_subscriptions": total_subs,
            "active_subscriptions": active_subs,
            "unique_parents": unique_parents,
            "students_with_subscription": students_with_sub,
            "total_students": total_students,
            "coverage_percentage": coverage_pct,
            "recent_subscriptions": recent,
        }
    )


@router.delete(
    "/subscriptions/{chat_id}",
    response_model=SuccessResponse[dict],
)
async def unsubscribe_chat(
    chat_id: int,
    _user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Deactivate all subscriptions for a given Telegram chat ID."""
    result = await db.execute(
        select(TelegramSub).where(
            TelegramSub.chat_id == chat_id,
            TelegramSub.is_active.is_(True),
        )
    )
    subs = result.scalars().all()
    if not subs:
        raise AttendXException(404, "NOT_FOUND", "No active subscriptions for this chat")

    for sub in subs:
        sub.is_active = False
    await db.commit()

    logger.info("telegram_unsubscribed", chat_id=chat_id, count=len(subs))
    return SuccessResponse(data={"deactivated": len(subs)})
