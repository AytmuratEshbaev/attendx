"""Telegram bot keyboard builders."""

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

__all__ = [
    "ReplyKeyboardRemove",
    "phone_request_keyboard",
    "main_menu_keyboard",
    "children_keyboard",
]


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with phone number share button."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Davomat", callback_data="menu_davomat")],
            [InlineKeyboardButton("📊 Haftalik", callback_data="menu_hafta")],
            [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="menu_sozlamalar")],
        ]
    )


def children_keyboard(students: list) -> InlineKeyboardMarkup:
    """Inline keyboard for selecting which children to subscribe to."""
    keyboard = [
        [
            InlineKeyboardButton(
                f"👤 {s.name} ({s.class_name or ''})",
                callback_data=f"child_{s.id}",
            )
        ]
        for s in students
    ]
    keyboard.append(
        [InlineKeyboardButton("✅ Hammasini tanlash", callback_data="child_all")]
    )
    return InlineKeyboardMarkup(keyboard)
