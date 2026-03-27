"""AccessGroup schemas — create/update/response for access groups and memberships."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.timetable import TimetableResponse


class DeviceBrief(BaseModel):
    id: int
    name: str
    ip_address: str
    is_active: bool

    model_config = {"from_attributes": True}


class StudentBrief(BaseModel):
    id: uuid.UUID
    name: str
    employee_no: str | None = None
    class_name: str | None = None
    face_registered: bool

    model_config = {"from_attributes": True}


class AccessGroupMembershipResponse(BaseModel):
    id: int
    student_id: uuid.UUID
    student: StudentBrief
    sync_status: str
    sync_error: str | None = None
    synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class AccessGroupCreate(BaseModel):
    name: str
    description: str | None = None
    timetable_id: int | None = None
    is_active: bool = True


class AccessGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    timetable_id: int | None = None
    is_active: bool | None = None


class AccessGroupResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    timetable_id: int | None = None
    timetable: TimetableResponse | None = None
    is_active: bool
    devices: list[DeviceBrief] = []
    students: list[AccessGroupMembershipResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    synced: int
    failed: int
    devices: int
