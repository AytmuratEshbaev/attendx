"""Timetable schemas — recurring and one-time schedule create/update/response."""

import json
from datetime import date, datetime, time
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class RecurringTimetableCreate(BaseModel):
    timetable_type: Literal["recurring"]
    name: str
    description: str | None = None
    weekdays: list[str] = Field(
        ...,
        description='E.g. ["Monday","Tuesday","Wednesday","Thursday","Friday"]',
    )
    start_time: time
    end_time: time
    is_active: bool = True

    @field_validator("weekdays", mode="before")
    @classmethod
    def parse_weekdays(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v  # type: ignore[return-value]


class OneTimeTimetableCreate(BaseModel):
    timetable_type: Literal["one_time"]
    name: str
    description: str | None = None
    date_from: date
    date_to: date
    ot_start_time: time
    ot_end_time: time
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self) -> "OneTimeTimetableCreate":
        if self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        return self


TimetableCreate = Annotated[
    Union[RecurringTimetableCreate, OneTimeTimetableCreate],
    Field(discriminator="timetable_type"),
]


class TimetableUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    # Recurring
    weekdays: list[str] | None = None
    start_time: time | None = None
    end_time: time | None = None
    # One-time
    date_from: date | None = None
    date_to: date | None = None
    ot_start_time: time | None = None
    ot_end_time: time | None = None


class TimetableResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    timetable_type: str
    is_active: bool
    # Recurring
    weekdays: list[str] | None = None
    start_time: time | None = None
    end_time: time | None = None
    # One-time
    date_from: date | None = None
    date_to: date | None = None
    ot_start_time: time | None = None
    ot_end_time: time | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("weekdays", mode="before")
    @classmethod
    def parse_weekdays(cls, v: object) -> list[str] | None:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return None
        return v  # type: ignore[return-value]
