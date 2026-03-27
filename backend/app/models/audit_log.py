"""Audit log model."""

import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False  # create/update/delete/login/logout
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )
