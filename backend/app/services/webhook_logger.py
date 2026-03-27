"""Webhook delivery logging and statistics."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_log import WebhookLog
from app.schemas.webhook_delivery import WebhookDeliveryResult

logger = structlog.get_logger()


class WebhookDeliveryLogger:
    """Logs all webhook delivery attempts and provides query methods."""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    async def log_delivery(
        self, session: AsyncSession, result: WebhookDeliveryResult
    ) -> WebhookLog:
        """Save delivery result to webhook_logs table."""
        log = WebhookLog(
            webhook_id=result.webhook_id,
            event_type=result.event_type,
            payload=result.payload,
            response_status=result.status_code or None,
            response_body=(
                result.response_body[:2000] if result.response_body else None
            ),
            attempts=result.attempt,
            success=result.success,
            delivery_id=result.delivery_id,
            duration_ms=result.duration_ms,
            error_message=result.error,
        )
        session.add(log)
        return log

    async def get_delivery_stats(
        self,
        webhook_id: UUID | None = None,
        days: int = 7,
    ) -> dict:
        """Get webhook delivery statistics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        async with self.db_session_factory() as session:
            base_filter = WebhookLog.created_at >= cutoff
            if webhook_id:
                base_filter = base_filter & (
                    WebhookLog.webhook_id == webhook_id
                )

            # Total counts
            total_result = await session.execute(
                select(func.count()).select_from(WebhookLog).where(base_filter)
            )
            total = total_result.scalar() or 0

            success_result = await session.execute(
                select(func.count())
                .select_from(WebhookLog)
                .where(base_filter & WebhookLog.success.is_(True))
            )
            successful = success_result.scalar() or 0

            failed = total - successful

            # Average response time
            avg_result = await session.execute(
                select(func.avg(WebhookLog.duration_ms))
                .where(base_filter & WebhookLog.duration_ms.isnot(None))
            )
            avg_response_time = avg_result.scalar() or 0

            # By event type
            event_stats_result = await session.execute(
                select(
                    WebhookLog.event_type,
                    func.count().label("total"),
                    func.sum(
                        func.cast(WebhookLog.success, type_=func.coalesce.type)
                        if False
                        else None
                    ),
                )
                .where(base_filter)
                .group_by(WebhookLog.event_type)
            )
            # Simplified: just get counts per event type
            by_event_type = {}
            event_rows = await session.execute(
                select(
                    WebhookLog.event_type,
                    func.count().label("total"),
                )
                .where(base_filter)
                .group_by(WebhookLog.event_type)
            )
            for row in event_rows:
                et = row[0]
                et_total = row[1]
                # Count successes for this event type
                et_success_result = await session.execute(
                    select(func.count())
                    .select_from(WebhookLog)
                    .where(
                        base_filter
                        & (WebhookLog.event_type == et)
                        & WebhookLog.success.is_(True)
                    )
                )
                et_success = et_success_result.scalar() or 0
                by_event_type[et] = {
                    "total": et_total,
                    "success": et_success,
                    "failed": et_total - et_success,
                }

            return {
                "total_deliveries": total,
                "successful": successful,
                "failed": failed,
                "success_rate": (
                    round(successful / total * 100, 2) if total > 0 else 0.0
                ),
                "avg_response_time_ms": round(float(avg_response_time), 2),
                "by_event_type": by_event_type,
            }

    async def get_recent_failures(
        self, limit: int = 20
    ) -> list[WebhookLog]:
        """Get most recent failed deliveries across all webhooks."""
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(WebhookLog)
                .where(WebhookLog.success.is_(False))
                .order_by(WebhookLog.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete webhook logs older than specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with self.db_session_factory() as session:
            result = await session.execute(
                delete(WebhookLog).where(WebhookLog.created_at < cutoff)
            )
            await session.commit()
            deleted = result.rowcount
            logger.info("webhook_logs_cleaned", deleted_count=deleted)
            return deleted
