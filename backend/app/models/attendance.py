"""Attendance log model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.student import Student


class AttendanceLog(TimestampMixin, Base):
    __tablename__ = "attendance_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False, index=True
    )
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"), nullable=True
    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(10), nullable=False  # entry / exit
    )
    verify_mode: Mapped[str] = mapped_column(
        String(20), default="face"
    )
    raw_event_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    picture_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    student: Mapped["Student"] = relationship(
        back_populates="attendance_logs", lazy="selectin"
    )
    device: Mapped["Device | None"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_attendance_student_time", "student_id", "event_time"),
    )
