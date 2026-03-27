"""Common response schemas used across all endpoints."""

import math
from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: Meta = Field(default_factory=Meta)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)


class PaginationInfo(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    meta: Meta = Field(default_factory=Meta)
    pagination: PaginationInfo

    @classmethod
    def create(
        cls,
        data: list,
        total: int,
        page: int,
        per_page: int,
    ) -> "PaginatedResponse":
        return cls(
            data=data,
            pagination=PaginationInfo(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page) if per_page else 0,
            ),
        )
