"""Shared helper functions for bot handlers."""

import asyncio

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from app.models.telegram_sub import TelegramSub

logger = structlog.get_logger()


async def _get_active_subs(session: AsyncSession, chat_id: int) -> list[TelegramSub]:
    """Get all active Telegram subscriptions for a chat."""
    result = await session.execute(
        select(TelegramSub).where(
            TelegramSub.chat_id == chat_id,
            TelegramSub.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().all()


async def get_subscriber_count(session: AsyncSession) -> int:
    """Get total active subscriber count."""
    result = await session.execute(
        select(func.count(TelegramSub.id)).where(
            TelegramSub.is_active == True  # noqa: E712
        )
    )
    return result.scalar() or 0


async def send_to_student_subscribers(
    bot: Bot,
    db_session_factory,
    student_id: str,
    message: str,
    parse_mode: str = "HTML",
) -> dict:
    """
    Send a message to all active subscribers of a student.

    Returns: {"sent": int, "failed": int, "errors": list}
    """
    sent = 0
    failed = 0
    errors: list[dict] = []

    async with db_session_factory() as session:
        result = await session.execute(
            select(TelegramSub).where(
                TelegramSub.student_id == student_id,
                TelegramSub.is_active == True,  # noqa: E712
            )
        )
        subs = result.scalars().all()

        for sub in subs:
            try:
                await bot.send_message(
                    chat_id=sub.chat_id,
                    text=message,
                    parse_mode=parse_mode,
                )
                sent += 1
                # Rate limiting: Telegram allows ~30 messages/second
                await asyncio.sleep(0.05)
            except Exception as e:
                failed += 1
                errors.append({"chat_id": sub.chat_id, "error": str(e)})
                logger.error(
                    "telegram_send_failed",
                    chat_id=sub.chat_id,
                    error=str(e),
                )

    return {"sent": sent, "failed": failed, "errors": errors}
