"""Attendance schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    class_name: str | None = None
    device_name: str | None = None
    event_time: datetime
    event_type: str
    verify_mode: str
    picture_url: str | None = None

    model_config = {"from_attributes": True}


class DeviceLiveEvent(BaseModel):
    """Attendance event fetched directly from a Hikvision device (no DB lookup)."""
    device_name: str
    employee_no: str
    student_name: str
    event_time: datetime
    event_type: str
    verify_mode: str
    picture_url: str | None = None


class AttendanceFilter(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    class_name: str | None = None
    student_id: uuid.UUID | None = None
    event_type: str | None = None


class AttendanceStats(BaseModel):
    total_students: int
    present_today: int
    absent_today: int
    attendance_percentage: float
    by_class: dict[str, dict]


class DailyAttendance(BaseModel):
    date: date
    present: int
    absent: int
    percentage: float
