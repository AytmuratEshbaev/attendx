"""
AttendX Telegram Bot — Real-time attendance notifications for parents.

Run: python -m bot.main
"""

import asyncio
import json
import signal
import sys
import uuid

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.telegram_sub import TelegramSub
from bot.handlers.attendance import davomat_command, hafta_command
from bot.handlers.common import (
    status_command,
    unknown_command,
    yordam_command,
)
from bot.handlers.settings import settings_callback, sozlamalar_command
from bot.handlers.start import (
    cancel_command,
    child_selected,
    phone_received,
    phone_text_received,
    start_command,
)
from bot.states import PHONE_VERIFY, SELECT_CHILD
from bot.templates import format_attendance_message

settings = get_settings()
logger = structlog.get_logger()


class AttendXBot:
    def __init__(self) -> None:
        self.app: Application | None = None
        self.db_session_factory = None
        self.redis: aioredis.Redis | None = None

    async def initialize(self) -> None:
        """Initialize database session factory, Redis, and Telegram Application."""
        # Use the existing async session factory from app.core.database
        self.db_session_factory = AsyncSessionLocal

        # Create a dedicated Redis client for the bot
        self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await self.redis.ping()
        logger.info("bot_redis_connected")

        # Build Telegram Application
        self.app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Store shared resources in bot_data for handler access
        self.app.bot_data["db_session_factory"] = self.db_session_factory
        self.app.bot_data["redis"] = self.redis

        self._register_handlers()
        logger.info("bot_initialized")

    def _register_handlers(self) -> None:
        """Register all command, message, and callback handlers."""
        # Registration conversation: /start → phone → (optional) child selection
        registration_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_command)],
            states={
                PHONE_VERIFY: [
                    MessageHandler(filters.CONTACT, phone_received),
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, phone_text_received
                    ),
                ],
                SELECT_CHILD: [
                    CallbackQueryHandler(child_selected, pattern=r"^child_"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_command)],
            per_user=True,
        )

        self.app.add_handler(registration_handler)
        self.app.add_handler(CommandHandler("davomat", davomat_command))
        self.app.add_handler(CommandHandler("hafta", hafta_command))
        self.app.add_handler(CommandHandler("sozlamalar", sozlamalar_command))
        self.app.add_handler(CommandHandler("yordam", yordam_command))
        self.app.add_handler(CommandHandler("status", status_command))

        # Settings inline-keyboard callbacks
        self.app.add_handler(
            CallbackQueryHandler(settings_callback, pattern=r"^settings_")
        )

        # Catch-all for unknown commands (must be last)
        self.app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    async def start(self) -> None:
        """Start the bot: long polling in DEBUG mode, webhook in production."""
        await self.initialize()

        if settings.LOG_LEVEL == "DEBUG":
            # Development — long polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            logger.info("bot_polling_started")

            # Run notification listener and heartbeat concurrently
            try:
                await asyncio.gather(
                    self._notification_listener(),
                    self._keep_alive(),
                )
            except asyncio.CancelledError:
                pass
        else:
            # Production — webhook mode
            if not settings.WEBHOOK_DOMAIN:
                raise RuntimeError(
                    "WEBHOOK_DOMAIN must be set in production (LOG_LEVEL != DEBUG)"
                )
            await self.app.run_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path=f"bot/{settings.TELEGRAM_BOT_TOKEN}",
                webhook_url=(
                    f"https://{settings.WEBHOOK_DOMAIN}"
                    f"/bot/{settings.TELEGRAM_BOT_TOKEN}"
                ),
            )

    async def _notification_listener(self) -> None:
        """Subscribe to Redis pub/sub and forward attendance events to parents."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("notifications:telegram")
        logger.info("bot_notification_listener_started")

        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._send_attendance_notification(data)
                    except Exception as e:
                        logger.error("notification_parse_error", error=str(e))
        except asyncio.CancelledError:
            await pubsub.unsubscribe("notifications:telegram")
            raise

    async def _send_attendance_notification(self, data: dict) -> None:
        """Send attendance notification to all active subscribers of the student."""
        student_id_str = data.get("student_id")
        if not student_id_str:
            return

        try:
            student_uuid = uuid.UUID(student_id_str)
        except ValueError:
            logger.error("invalid_student_id_in_notification", value=student_id_str)
            return

        async with self.db_session_factory() as session:
            result = await session.execute(
                select(TelegramSub).where(
                    TelegramSub.student_id == student_uuid,
                    TelegramSub.is_active == True,  # noqa: E712
                )
            )
            subs = result.scalars().all()

            message_text = format_attendance_message(data)

            for sub in subs:
                try:
                    await self.app.bot.send_message(
                        chat_id=sub.chat_id,
                        text=message_text,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.error(
                        "telegram_notification_failed",
                        chat_id=sub.chat_id,
                        student_id=student_id_str,
                        error=str(e),
                    )

    async def _keep_alive(self) -> None:
        """Periodic heartbeat log to indicate the bot is alive."""
        while True:
            await asyncio.sleep(60)
            logger.debug("bot_heartbeat", status="alive")

    async def shutdown(self) -> None:
        """Graceful shutdown: stop polling, close connections."""
        logger.info("bot_shutting_down")
        if self.app:
            if self.app.updater and self.app.updater.running:
                await self.app.updater.stop()
            if self.app.running:
                await self.app.stop()
            await self.app.shutdown()
        if self.redis:
            await self.redis.aclose()
        logger.info("bot_stopped")


def main() -> None:
    bot = AttendXBot()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register OS signal handlers (POSIX only; Windows doesn't support this)
    if sys.platform != "win32":
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.ensure_future(bot.shutdown(), loop=loop),
            )

    try:
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        loop.run_until_complete(bot.shutdown())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
