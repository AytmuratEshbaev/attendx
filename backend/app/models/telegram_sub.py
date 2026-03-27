"""Telegram subscription model."""

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TelegramSub(TimestampMixin, Base):
    __tablename__ = "telegram_subs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
