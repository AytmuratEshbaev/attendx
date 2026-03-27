"""Telegram bot /yordam, /status, and unknown command handlers."""

from datetime import datetime

import structlog
from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.models.device import Device
from bot.helpers import _get_active_subs

logger = structlog.get_logger()


async def yordam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yordam — Show help message."""
    await update.message.reply_text(
        "❓ <b>AttendX Bot — Yordam</b>\n\n"
        "📋 /davomat — Bugungi davomat holati\n"
        "📊 /hafta — Haftalik davomat hisoboti\n"
        "⚙️ /sozlamalar — Xabar olish sozlamalari\n"
        "📱 /start — Qayta ro'yxatdan o'tish\n"
        "ℹ️ /status — Bot holati\n"
        "❓ /yordam — Shu yordam xabari\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "Farzandingiz maktabga kelganda yoki ketganda "
        "avtomatik xabar olasiz.\n\n"
        "<b>Muammo bo'lsa:</b>\n"
        "Maktab administratori bilan bog'laning.",
        parse_mode="HTML",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — Show bot and system status."""
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    redis = context.bot_data["redis"]

    async with db_session_factory() as session:
        subs = await _get_active_subs(session, chat_id)

        total_result = await session.execute(
            select(func.count(Device.id)).where(Device.is_active == True)  # noqa: E712
        )
        total_devices: int = total_result.scalar() or 0

        # Check online devices from Redis (key: device:{id}:online = "1")
        online_count = 0
        for device_id in range(1, total_devices + 1):
            status = await redis.get(f"device:{device_id}:online")
            if status == "1":
                online_count += 1

        await update.message.reply_text(
            f"ℹ️ <b>AttendX Bot Status</b>\n\n"
            f"🤖 Bot: ✅ Ishlayapti\n"
            f"📡 Terminallar: {online_count}/{total_devices} online\n"
            f"👤 Sizning obunalar: {len(subs)} ta\n"
            f"🕐 Server vaqti: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML",
        )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Noma'lum buyruq.\n/yordam — barcha buyruqlar ro'yxati"
    )
