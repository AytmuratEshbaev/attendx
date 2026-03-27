"""SQLAlchemy 2.0 async models — import all for Alembic discovery."""

from app.models.access_group import (
    AccessGroup,
    AccessGroupDevicePlanTemplate,
    AccessGroupStudent,
)
from app.models.api_key import APIKey
from app.models.attendance import AttendanceLog
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.category import Category
from app.models.device import Device
from app.models.student import Student
from app.models.telegram_sub import TelegramSub
from app.models.timetable import Timetable
from app.models.user import User
from app.models.webhook import Webhook
from app.models.webhook_log import WebhookLog

__all__ = [
    "Base",
    "AccessGroup",
    "AccessGroupStudent",
    "AccessGroupDevicePlanTemplate",
    "APIKey",
    "AttendanceLog",
    "AuditLog",
    "Category",
    "Device",
    "Student",
    "TelegramSub",
    "Timetable",
    "User",
    "Webhook",
    "WebhookLog",
]
