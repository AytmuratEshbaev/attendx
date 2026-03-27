"""Webhook delivery data models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class WebhookDeliveryResult:
    """Result of a single webhook delivery attempt."""

    delivery_id: str
    webhook_id: UUID
    event_type: str
    success: bool
    status_code: int
    response_body: str = ""
    duration_ms: int = 0
    error: str | None = None
    attempt: int = 1
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
