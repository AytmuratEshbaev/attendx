"""Telegram notification message templates (Uzbek language)."""

from datetime import datetime


def format_attendance_message(data: dict) -> str:
    """
    Format attendance notification for Telegram.

    Entry: ✅ Ali Valiyev maktabga keldi
    Exit:  🏠 Ali Valiyev maktabdan ketdi
    """
    event_type = data.get("event_type", "entry")
    student_name = data.get("student_name", "Noma'lum")
    class_name = data.get("class_name", "")
    event_time = data.get("event_time", "")
    device_name = data.get("device_name", "")

    try:
        dt = datetime.fromisoformat(event_time)
        time_str = dt.strftime("%H:%M")
    except (ValueError, TypeError):
        time_str = event_time

    if event_type == "entry":
        return (
            f"✅ <b>{student_name}</b> maktabga keldi\n"
            f"📚 {class_name}\n"
            f"🕐 {time_str}\n"
            f"📍 {device_name}"
        )
    else:
        return (
            f"🏠 <b>{student_name}</b> maktabdan ketdi\n"
            f"📚 {class_name}\n"
            f"🕐 {time_str}\n"
            f"📍 {device_name}"
        )


def format_late_notification(data: dict, threshold_time: str = "08:30") -> str:
    """Format late arrival notification."""
    return (
        f"⚠️ <b>{data['student_name']}</b> kechikib keldi\n"
        f"📚 {data['class_name']}\n"
        f"🕐 {data.get('arrival_time', '')} (belgilangan: {threshold_time})\n"
        f"📍 {data.get('device_name', '')}"
    )


def format_absent_notification(
    student_name: str, class_name: str, date_str: str
) -> str:
    """Format absence notification (sent at end of school day)."""
    return (
        f"❌ <b>{student_name}</b> bugun maktabga kelmadi\n"
        f"📚 {class_name}\n"
        f"📅 {date_str}"
    )


def format_weekly_summary(
    student_name: str, class_name: str, present: int, total: int
) -> str:
    """Format weekly summary notification (sent on Friday/Saturday)."""
    percentage = (present / total * 100) if total > 0 else 0
    bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))

    return (
        f"📊 <b>Haftalik hisobot</b>\n\n"
        f"👤 {student_name} ({class_name})\n"
        f"📈 {bar} {percentage:.0f}%\n"
        f"✅ Keldi: {present} kun\n"
        f"❌ Kelmadi: {total - present} kun\n"
        f"📅 Jami: {total} ish kuni"
    )
