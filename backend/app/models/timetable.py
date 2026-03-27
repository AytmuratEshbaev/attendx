"""Timetable model — recurring and one-time access schedules."""

from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Timetable(TimestampMixin, Base):
    __tablename__ = "timetables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timetable_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # recurring | one_time
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Recurring fields
    weekdays: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON: ["Monday","Tuesday",...]
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # One-time fields
    date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    ot_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    ot_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
