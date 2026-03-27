"""Device schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DeviceBase(BaseModel):
    name: str
    ip_address: str
    port: int = 80
    username: str = "admin"
    is_entry: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=100)

    @field_validator("ip_address", mode="before")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        cleaned = InputSanitizer.sanitize_string(v, max_length=45)
        if not InputSanitizer.validate_ip_address(cleaned):
            raise ValueError("Invalid IPv4 address format")
        return cleaned

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=50)


class DeviceCreate(DeviceBase):
    password: str = Field(..., min_length=1)  # plain text, will be encrypted


class DeviceUpdate(BaseModel):
    name: str | None = None
    ip_address: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    is_entry: bool | None = None
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def sanitize_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        return InputSanitizer.sanitize_string(v, max_length=100)

    @field_validator("ip_address", mode="before")
    @classmethod
    def validate_ip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from app.core.validation import InputSanitizer

        cleaned = InputSanitizer.sanitize_string(v, max_length=45)
        if not InputSanitizer.validate_ip_address(cleaned):
            raise ValueError("Invalid IPv4 address format")
        return cleaned


class DeviceResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    is_entry: bool
    is_active: bool
    last_online_at: datetime | None = None
    model: str | None = None
    serial_number: str | None = None

    model_config = {"from_attributes": True}


class DeviceHealth(BaseModel):
    id: int
    name: str
    is_online: bool
    last_online_at: datetime | None = None
    response_time_ms: float | None = None
