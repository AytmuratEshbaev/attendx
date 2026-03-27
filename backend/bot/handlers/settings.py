"""Telegram bot settings command and callback handlers."""

import uuid

import structlog
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.models.student import Student
from app.models.telegram_sub import TelegramSub
from bot.helpers import _get_active_subs

logger = structlog.get_logger()


async def sozlamalar_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    /sozlamalar — Show settings menu with inline keyboard.

    Displays per-child notification toggle buttons plus unsubscribe option.
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]

    async with db_session_factory() as session:
        subs = await _get_active_subs(session, chat_id)

        if not subs:
            await update.message.reply_text(
                "❌ Siz hali ro'yxatdan o'tmagansiz.\n/start bosing."
            )
            return

        keyboard = []
        status_lines = []

        for sub in subs:
            if sub.student_id is None:
                continue
            student = await session.get(Student, sub.student_id)
            if not student:
                continue

            icon = "🔔" if sub.is_active else "🔕"
            btn_label = (
                f"🔔 Xabarlarni o'chirish — {student.name}"
                if sub.is_active
                else f"🔕 Xabarlarni yoqish — {student.name}"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        btn_label,
                        callback_data=f"settings_toggle_{sub.student_id}",
                    )
                ]
            )
            status_lines.append(f"{icon} {student.name} ({student.class_name or '—'})")

        keyboard.append(
            [InlineKeyboardButton("🗑 Ro'yxatdan chiqish", callback_data="settings_unsubscribe")]
        )
        keyboard.append(
            [InlineKeyboardButton("📱 Farzand qo'shish", callback_data="settings_add_child")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"Xabar olish holati:\n" + "\n".join(status_lines),
            reply_markup=reply_markup,
            parse_mode="HTML",
        )


async def settings_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle settings inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    action: str = query.data
    db_session_factory = context.bot_data["db_session_factory"]

    async with db_session_factory() as session:
        if action.startswith("settings_toggle_"):
            student_id_str = action.replace("settings_toggle_", "")
            try:
                student_uuid = uuid.UUID(student_id_str)
            except ValueError:
                await query.edit_message_text("❌ Xatolik yuz berdi.")
                return

            result = await session.execute(
                select(TelegramSub).where(
                    TelegramSub.chat_id == chat_id,
                    TelegramSub.student_id == student_uuid,
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.is_active = not sub.is_active
                await session.commit()
                status = "yoqildi 🔔" if sub.is_active else "o'chirildi 🔕"
                await query.edit_message_text(
                    f"✅ Xabarlar {status}\n\n/sozlamalar — qayta ko'rish"
                )

        elif action == "settings_unsubscribe":
            result = await session.execute(
                select(TelegramSub).where(TelegramSub.chat_id == chat_id)
            )
            subs = result.scalars().all()
            for sub in subs:
                sub.is_active = False
            await session.commit()
            logger.info("telegram_unsubscribed", chat_id=chat_id)
            await query.edit_message_text(
                "✅ Ro'yxatdan chiqdingiz.\nQayta ro'yxatdan o'tish: /start"
            )

        elif action == "settings_add_child":
            await query.edit_message_text(
                "Yangi farzand qo'shish uchun /start bosing va "
                "telefon raqamingizni kiriting."
            )
