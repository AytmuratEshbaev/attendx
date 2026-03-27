"""Student schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    class_name: str | None = None
    parent_phone: str | None = Field(None, pattern=r"^\+?\d{9,20}$")
    external_id: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=200)

    @field_validator("class_name", mode="before")
    @classmethod
    def sanitize_class_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=50)

    @field_validator("external_id", mode="before")
    @classmethod
    def sanitize_external_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=100)


class StudentCreate(StudentBase):
    employee_no: str = Field(..., min_length=1, max_length=50)
    category_id: int | None = None

    @field_validator("employee_no", mode="before")
    @classmethod
    def sanitize_employee_no(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=50)


class StudentUpdate(BaseModel):
    name: str | None = None
    class_name: str | None = None
    category_id: int | None = None
    parent_phone: str | None = Field(None, pattern=r"^\+?\d{9,20}$")
    external_id: str | None = None
    employee_no: str | None = None
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=200)

    @field_validator("class_name", mode="before")
    @classmethod
    def sanitize_class_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=50)


class CategoryBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class StudentResponse(BaseModel):
    id: uuid.UUID
    external_id: str | None = None
    employee_no: str | None = None
    name: str
    class_name: str | None = None
    category_id: int | None = None
    category: CategoryBrief | None = None
    parent_phone: str | None = None
    face_registered: bool
    face_image_path: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudentImportRow(BaseModel):
    name: str
    employee_no: str
    class_name: str
    parent_phone: str | None = None
    external_id: str | None = None


class StudentImportResult(BaseModel):
    total: int
    created: int
    updated: int
    errors: list[str]
