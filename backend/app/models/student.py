"""Student model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import AttendanceLog
    from app.models.category import Category


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    employee_no: Mapped[str | None] = mapped_column(
        String(50), unique=True, index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    class_name: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    face_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    face_image_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(
        back_populates="student", lazy="selectin"
    )
    category: Mapped["Category | None"] = relationship(
        back_populates="students", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_students_name", "name"),
    )
