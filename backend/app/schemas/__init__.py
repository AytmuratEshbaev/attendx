"""Pydantic v2 request/response schemas."""

from app.schemas.attendance import (
    AttendanceFilter,
    AttendanceResponse,
    AttendanceStats,
    DailyAttendance,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import (
    ErrorResponse,
    Meta,
    PaginatedResponse,
    SuccessResponse,
)
from app.schemas.device import (
    DeviceCreate,
    DeviceHealth,
    DeviceResponse,
    DeviceUpdate,
)
from app.schemas.student import (
    StudentCreate,
    StudentImportResult,
    StudentResponse,
    StudentUpdate,
)
from app.schemas.webhook import (
    WebhookCreate,
    WebhookLogResponse,
    WebhookResponse,
    WebhookUpdate,
)

__all__ = [
    "ChangePasswordRequest",
    "AttendanceFilter",
    "AttendanceResponse",
    "AttendanceStats",
    "DailyAttendance",
    "DeviceCreate",
    "DeviceHealth",
    "DeviceResponse",
    "DeviceUpdate",
    "ErrorResponse",
    "LoginRequest",
    "Meta",
    "PaginatedResponse",
    "RefreshRequest",
    "StudentCreate",
    "StudentImportResult",
    "StudentResponse",
    "StudentUpdate",
    "SuccessResponse",
    "TokenResponse",
    "UserResponse",
    "WebhookCreate",
    "WebhookLogResponse",
    "WebhookResponse",
    "WebhookUpdate",
]
