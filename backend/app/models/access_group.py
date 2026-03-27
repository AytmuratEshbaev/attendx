"""AccessGroup models — groups devices and students with a timetable."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.student import Student
    from app.models.timetable import Timetable


# Junction table: AccessGroup <-> Device (many-to-many)
access_group_devices = Table(
    "access_group_devices",
    Base.metadata,
    Column(
        "access_group_id",
        Integer,
        ForeignKey("access_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "device_id",
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AccessGroup(TimestampMixin, Base):
    __tablename__ = "access_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timetable_id: Mapped[int | None] = mapped_column(
        ForeignKey("timetables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    timetable: Mapped["Timetable | None"] = relationship(
        "Timetable",
        lazy="selectin",
    )
    devices: Mapped[list["Device"]] = relationship(
        "Device",
        secondary=access_group_devices,
        lazy="selectin",
    )
    students: Mapped[list["AccessGroupStudent"]] = relationship(
        "AccessGroupStudent",
        back_populates="access_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    plan_templates: Mapped[list["AccessGroupDevicePlanTemplate"]] = relationship(
        "AccessGroupDevicePlanTemplate",
        back_populates="access_group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AccessGroupStudent(Base):
    """Membership record — student in an access group with sync tracking."""

    __tablename__ = "access_group_students"
    __table_args__ = (
        UniqueConstraint(
            "access_group_id", "student_id", name="uq_access_group_student"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_group_id: Mapped[int] = mapped_column(
        ForeignKey("access_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending | synced | failed
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    access_group: Mapped["AccessGroup"] = relationship(
        "AccessGroup", back_populates="students"
    )
    student: Mapped["Student"] = relationship("Student", lazy="selectin")


class AccessGroupDevicePlanTemplate(Base):
    """Stores the plan template ID for each (access_group, device) pair."""

    __tablename__ = "access_group_device_plan_templates"
    __table_args__ = (
        UniqueConstraint(
            "access_group_id",
            "device_id",
            name="uq_access_group_device_template",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_group_id: Mapped[int] = mapped_column(
        ForeignKey("access_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_template_id: Mapped[int] = mapped_column(Integer, nullable=False)

    access_group: Mapped["AccessGroup"] = relationship(
        "AccessGroup", back_populates="plan_templates"
    )
