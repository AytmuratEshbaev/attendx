"""Webhook schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class WebhookBase(BaseModel):
    url: str
    events: list[str]
    description: str | None = None

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        if not InputSanitizer.validate_url(v):
            raise ValueError(
                "URL must start with http:// or https:// and be a valid URL"
            )
        return v

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=500)


class WebhookCreate(WebhookBase):
    secret: str | None = None  # auto-generated if not provided


class WebhookUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        if not InputSanitizer.validate_url(v):
            raise ValueError(
                "URL must start with http:// or https:// and be a valid URL"
            )
        return v

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=500)


class WebhookResponse(BaseModel):
    id: uuid.UUID
    url: str
    events: list | dict  # JSON field
    is_active: bool
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookLogResponse(BaseModel):
    id: uuid.UUID
    webhook_id: uuid.UUID
    event_type: str
    payload: dict
    response_status: int | None = None
    attempts: int
    success: bool
    delivery_id: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
