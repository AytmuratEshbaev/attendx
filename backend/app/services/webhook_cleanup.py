"""Periodic cleanup of old webhook logs and dead letters."""

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import delete

from app.models.webhook_log import WebhookLog

logger = structlog.get_logger()


class WebhookCleanup:
    """Periodic cleanup of old webhook logs and dead letters."""

    async def cleanup_logs(self, db_session_factory, days: int = 30) -> int:
        """Delete webhook_logs older than X days. Run daily via cron."""
        async with db_session_factory() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            result = await session.execute(
                delete(WebhookLog).where(WebhookLog.created_at < cutoff)
            )
            await session.commit()
            deleted = result.rowcount
            logger.info(
                "webhook_logs_cleaned_up", deleted_count=deleted, days=days
            )
            return deleted

    async def cleanup_dead_letters(
        self, redis_client, max_items: int = 1000
    ) -> None:
        """Trim dead letter queue to max items."""
        await redis_client.ltrim("webhook:dead_letter", 0, max_items - 1)
