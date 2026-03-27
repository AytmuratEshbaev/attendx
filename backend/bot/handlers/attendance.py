"""Telegram bot attendance command handlers (/davomat, /hafta)."""

from datetime import date, timedelta

import structlog
from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.models.attendance import AttendanceLog
from app.models.device import Device
from app.models.student import Student
from bot.helpers import _get_active_subs

logger = structlog.get_logger()


async def davomat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /davomat — Show today's attendance for all subscribed children.

    Output per child:
        👤 Ali Valiyev (5-A)
        ✅ Kirish: 08:45 — Asosiy kirish
        🏠 Chiqish: 14:30 — Orqa chiqish
        ⏳ Hali chiqmagan  (if last event is entry)
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

        today = date.today()
        response_parts = [
            f"📋 <b>Bugungi davomat</b> — {today.strftime('%Y-%m-%d')}\n"
        ]

        for sub in subs:
            if sub.student_id is None:
                continue
            student = await session.get(Student, sub.student_id)
            if not student:
                continue

            result = await session.execute(
                select(AttendanceLog)
                .where(
                    AttendanceLog.student_id == student.id,
                    func.date(AttendanceLog.event_time) == today,
                )
                .order_by(AttendanceLog.event_time.asc())
            )
            records = result.scalars().all()

            part = f"\n👤 <b>{student.name}</b> ({student.class_name or '—'})\n"

            if not records:
                part += "❌ Bugun kelmagan\n"
            else:
                for record in records:
                    time_str = record.event_time.strftime("%H:%M")
                    if record.event_type == "entry":
                        part += f"✅ Kirish: {time_str}"
                    else:
                        part += f"🏠 Chiqish: {time_str}"

                    if record.device_id is not None:
                        device = await session.get(Device, record.device_id)
                        if device:
                            part += f" — {device.name}"
                    part += "\n"

                if records[-1].event_type == "entry":
                    part += "⏳ Hali chiqmagan\n"

            response_parts.append(part)

        await update.message.reply_text(
            "\n".join(response_parts),
            parse_mode="HTML",
        )


async def hafta_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /hafta — Show weekly attendance report (Mon–Sun of current week).

    Output per child:
        👤 Ali Valiyev (5-A)
        Du  13.02  ✅ Keldi (08:45)
        ...
        📈 Davomat: 5/6 kun (83.3%)
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

        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        day_names_uz = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]

        response_parts = [
            f"📊 <b>Haftalik hisobot</b> — "
            f"{monday.strftime('%d.%m')} – {sunday.strftime('%d.%m.%Y')}\n"
        ]

        for sub in subs:
            if sub.student_id is None:
                continue
            student = await session.get(Student, sub.student_id)
            if not student:
                continue

            result = await session.execute(
                select(AttendanceLog)
                .where(
                    AttendanceLog.student_id == student.id,
                    func.date(AttendanceLog.event_time) >= monday,
                    func.date(AttendanceLog.event_time) <= sunday,
                    AttendanceLog.event_type == "entry",
                )
                .order_by(AttendanceLog.event_time.asc())
            )
            entries = result.scalars().all()

            # Map date → first entry time string
            entry_dates: dict[date, str] = {}
            for entry in entries:
                d = entry.event_time.date()
                if d not in entry_dates:
                    entry_dates[d] = entry.event_time.strftime("%H:%M")

            part = f"\n👤 <b>{student.name}</b> ({student.class_name or '—'})\n"
            present_days = 0
            school_days = 0

            for i in range(7):
                day = monday + timedelta(days=i)
                day_name = day_names_uz[i]
                day_str = day.strftime("%d.%m")

                if i >= 5:  # Saturday, Sunday
                    part += f"{day_name}  {day_str}  — Dam olish\n"
                elif day > today:
                    part += f"{day_name}  {day_str}  ⏳ Hali kelmagan\n"
                else:
                    school_days += 1
                    if day in entry_dates:
                        present_days += 1
                        part += f"{day_name}  {day_str}  ✅ Keldi ({entry_dates[day]})\n"
                    else:
                        part += f"{day_name}  {day_str}  ❌ Kelmadi\n"

            percentage = (present_days / school_days * 100) if school_days > 0 else 0.0
            part += f"\n📈 Davomat: {present_days}/{school_days} kun ({percentage:.1f}%)\n"

            response_parts.append(part)

        await update.message.reply_text(
            "\n".join(response_parts),
            parse_mode="HTML",
        )
