"""Telegram bot /start command and phone verification handlers."""

import uuid

import structlog
from sqlalchemy import select
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from app.models.student import Student
from app.models.telegram_sub import TelegramSub
from bot.states import PHONE_VERIFY, SELECT_CHILD
from bot.utils import generate_phone_variants, is_valid_phone, normalize_phone

logger = structlog.get_logger()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /start command — begin registration flow.

    Flow:
    1. Greet the user
    2. Check if already registered
    3. If registered → show welcome back message with children list
    4. If not registered → ask for phone number
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]

    async with db_session_factory() as session:
        result = await session.execute(
            select(TelegramSub).where(
                TelegramSub.chat_id == chat_id,
                TelegramSub.is_active == True,  # noqa: E712
            )
        )
        existing = result.scalars().all()

        if existing:
            student_names = []
            for sub in existing:
                student = await session.get(Student, sub.student_id)
                if student:
                    student_names.append(
                        f"👤 {student.name} ({student.class_name or ''})"
                    )

            names_text = "\n".join(student_names)
            await update.message.reply_text(
                f"👋 Xush kelibsiz!\n\n"
                f"Siz allaqachon ro'yxatdan o'tgansiz.\n"
                f"Farzandlaringiz:\n{names_text}\n\n"
                f"📋 /davomat — Bugungi davomat\n"
                f"📊 /hafta — Haftalik hisobot\n"
                f"⚙️ /sozlamalar — Sozlamalar\n"
                f"❓ /yordam — Yordam",
                parse_mode="HTML",
            )
            return ConversationHandler.END

        keyboard = [
            [KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )

        await update.message.reply_text(
            "👋 <b>AttendX</b> — Davomat Monitoring tizimiga xush kelibsiz!\n\n"
            "Farzandingizning maktabga kelish/ketish xabarlarini olish uchun "
            "telefon raqamingizni tasdiqlang.\n\n"
            "Quyidagi tugmani bosing yoki raqamingizni +998XXXXXXXXX formatda yozing:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return PHONE_VERIFY


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle shared contact (phone number button pressed)."""
    contact = update.message.contact
    phone = normalize_phone(contact.phone_number)
    return await _verify_phone(update, context, phone)


async def phone_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle manually typed phone number."""
    phone = update.message.text.strip()
    phone = normalize_phone(phone)

    if not is_valid_phone(phone):
        await update.message.reply_text(
            "❌ Noto'g'ri format. Iltimos +998XXXXXXXXX formatda yozing.\n"
            "Masalan: +998901234567"
        )
        return PHONE_VERIFY

    return await _verify_phone(update, context, phone)


async def _verify_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str
) -> int:
    """
    Core phone verification logic.

    1. Search students where parent_phone matches (multiple format variants)
    2. If found one → auto-link and confirm
    3. If found many → show child selection keyboard
    4. If not found → error message
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]

    async with db_session_factory() as session:
        phone_variants = generate_phone_variants(phone)

        result = await session.execute(
            select(Student).where(
                Student.parent_phone.in_(phone_variants),
                Student.is_active == True,  # noqa: E712
            )
        )
        students = result.scalars().all()

        if not students:
            await update.message.reply_text(
                "❌ Bu telefon raqam bazada topilmadi.\n\n"
                "Iltimos, maktab administratori bilan bog'laning va "
                "telefon raqamingiz tizimga kiritilganligini tekshiring.\n\n"
                "Qayta urinish uchun /start bosing.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

        if len(students) == 1:
            student = students[0]
            sub = TelegramSub(
                chat_id=chat_id,
                phone=phone,
                student_id=student.id,
                is_active=True,
            )
            session.add(sub)
            await session.commit()

            logger.info(
                "telegram_registered",
                chat_id=chat_id,
                student_id=str(student.id),
            )
            await update.message.reply_text(
                f"✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
                f"👤 <b>{student.name}</b>\n"
                f"📚 Sinf: {student.class_name or '—'}\n\n"
                f"Endi farzandingiz maktabga kelganda va ketganda xabar olasiz.\n\n"
                f"📋 /davomat — Bugungi davomat\n"
                f"📊 /hafta — Haftalik hisobot",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML",
            )
            return ConversationHandler.END

        # Multiple children — ask which ones to subscribe
        context.user_data["students"] = {str(s.id): s for s in students}
        context.user_data["phone"] = phone

        keyboard = []
        for student in students:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"👤 {student.name} ({student.class_name or ''})",
                        callback_data=f"child_{student.id}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("✅ Hammasini tanlash", callback_data="child_all")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📱 Telefon raqamingizga {len(students)} ta farzand topildi.\n"
            f"Qaysi biri uchun xabar olmoqchisiz?",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return SELECT_CHILD


async def child_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle child selection callback."""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    phone = context.user_data.get("phone", "")
    students: dict = context.user_data.get("students", {})
    db_session_factory = context.bot_data["db_session_factory"]

    selection = query.data  # "child_{uuid}" or "child_all"

    async with db_session_factory() as session:
        linked = []

        if selection == "child_all":
            for _sid, student in students.items():
                sub = TelegramSub(
                    chat_id=chat_id,
                    phone=phone,
                    student_id=student.id,
                    is_active=True,
                )
                session.add(sub)
                linked.append(f"👤 {student.name} ({student.class_name or ''})")
        else:
            student_id_str = selection.replace("child_", "")
            student = students.get(student_id_str)
            if student:
                sub = TelegramSub(
                    chat_id=chat_id,
                    phone=phone,
                    student_id=student.id,
                    is_active=True,
                )
                session.add(sub)
                linked.append(f"👤 {student.name} ({student.class_name or ''})")

        await session.commit()

        logger.info(
            "telegram_registered",
            chat_id=chat_id,
            linked_count=len(linked),
        )

        names_text = "\n".join(linked)
        await query.edit_message_text(
            f"✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
            f"{names_text}\n\n"
            f"Endi xabar olasiz.\n\n"
            f"📋 /davomat — Bugungi davomat\n"
            f"📊 /hafta — Haftalik hisobot",
            parse_mode="HTML",
        )

    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel ongoing registration conversation."""
    await update.message.reply_text(
        "❌ Bekor qilindi. Qayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
