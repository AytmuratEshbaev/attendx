"""Webhook retry manager using Redis sorted sets."""

import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import structlog

from app.models.webhook import Webhook
from app.models.webhook_log import WebhookLog

logger = structlog.get_logger()


class WebhookRetryManager:
    """
    Manages failed webhook delivery retries using Redis sorted sets.

    Strategy: Exponential backoff with 3 attempts
    - Attempt 1: Immediate (in dispatch_event)
    - Attempt 2: After 10 seconds
    - Attempt 3: After 60 seconds
    - Attempt 4: After 300 seconds (5 min) -- final attempt

    After all retries exhausted -> mark as permanently failed, dead letter.
    """

    RETRY_QUEUE_KEY = "webhook:retry:queue"
    MAX_RETRIES = 3
    RETRY_DELAYS = [10, 60, 300]  # seconds

    def __init__(self, webhook_engine, db_session_factory, redis_client):
        self.engine = webhook_engine
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.running = False

    async def queue_retry(
        self,
        webhook_id: str,
        event_type: str,
        payload: dict,
        attempt: int,
    ) -> None:
        """Queue a failed delivery for retry in Redis sorted set."""
        if attempt > self.MAX_RETRIES:
            await self._handle_permanent_failure(
                webhook_id, event_type, payload
            )
            return

        delay = (
            self.RETRY_DELAYS[attempt - 1]
            if attempt <= len(self.RETRY_DELAYS)
            else self.RETRY_DELAYS[-1]
        )
        retry_at = datetime.now(timezone.utc).timestamp() + delay

        retry_data = json.dumps(
            {
                "webhook_id": str(webhook_id),
                "event_type": event_type,
                "payload": payload,
                "attempt": attempt + 1,
                "original_timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_id": str(uuid4()),
            }
        )

        await self.redis.zadd(
            self.RETRY_QUEUE_KEY, {retry_data: retry_at}
        )
        logger.info(
            "webhook_retry_queued",
            webhook_id=str(webhook_id),
            attempt=attempt + 1,
            retry_in_seconds=delay,
        )

    async def start_retry_processor(self) -> None:
        """Background loop that processes retry queue every 5 seconds."""
        self.running = True
        while self.running:
            try:
                await self._process_pending_retries()
            except Exception as e:
                logger.error("retry_processor_error", error=str(e))
            await asyncio.sleep(5)

    async def stop(self) -> None:
        """Stop the retry processor loop."""
        self.running = False

    async def _process_pending_retries(self) -> None:
        """Process all retries that are due."""
        now = datetime.now(timezone.utc).timestamp()

        items = await self.redis.zrangebyscore(
            self.RETRY_QUEUE_KEY, "-inf", str(now), start=0, num=50
        )

        for item in items:
            removed = await self.redis.zrem(self.RETRY_QUEUE_KEY, item)
            if not removed:
                continue  # Another worker already took it

            retry_data = json.loads(item)
            await self._execute_retry(retry_data)

    async def _execute_retry(self, retry_data: dict) -> None:
        """Execute a single retry attempt."""
        webhook_id = retry_data["webhook_id"]
        event_type = retry_data["event_type"]
        payload = retry_data["payload"]
        attempt = retry_data["attempt"]

        async with self.db_session_factory() as session:
            webhook = await session.get(Webhook, webhook_id)
            if not webhook or not webhook.is_active:
                logger.info(
                    "webhook_retry_skipped_inactive",
                    webhook_id=webhook_id,
                )
                return

            result = await self.engine.deliver(webhook, event_type, payload)
            result.attempt = attempt

            # Log the attempt
            log = WebhookLog(
                webhook_id=result.webhook_id,
                event_type=result.event_type,
                payload=result.payload,
                response_status=result.status_code or None,
                response_body=(
                    result.response_body[:2000]
                    if result.response_body
                    else None
                ),
                attempts=result.attempt,
                success=result.success,
                delivery_id=result.delivery_id,
                duration_ms=result.duration_ms,
                error_message=result.error,
            )
            session.add(log)
            await session.commit()

            if result.success:
                await self.engine.circuit_breaker.record_success(
                    str(webhook_id)
                )
                logger.info(
                    "webhook_retry_success",
                    webhook_id=webhook_id,
                    attempt=attempt,
                )
            else:
                await self.engine.circuit_breaker.record_failure(
                    str(webhook_id)
                )
                await self.queue_retry(
                    webhook_id, event_type, payload, attempt
                )

    async def _handle_permanent_failure(
        self,
        webhook_id: str,
        event_type: str,
        payload: dict,
    ) -> None:
        """Handle permanently failed webhook delivery."""
        logger.error(
            "webhook_delivery_permanently_failed",
            webhook_id=webhook_id,
            event_type=event_type,
        )

        dead_letter = json.dumps(
            {
                "webhook_id": webhook_id,
                "event_type": event_type,
                "payload": payload,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "max_retries_exceeded": True,
            }
        )
        await self.redis.lpush("webhook:dead_letter", dead_letter)
        # Keep only last 1000 dead letters
        await self.redis.ltrim("webhook:dead_letter", 0, 999)

    async def get_retry_queue_size(self) -> int:
        """Get number of items in retry queue."""
        return await self.redis.zcard(self.RETRY_QUEUE_KEY)

    async def get_dead_letter_count(self) -> int:
        """Get number of permanently failed deliveries."""
        return await self.redis.llen("webhook:dead_letter")

    async def get_dead_letters(
        self, start: int = 0, count: int = 20
    ) -> list[dict]:
        """Get dead letter items."""
        items = await self.redis.lrange(
            "webhook:dead_letter", start, start + count - 1
        )
        return [json.loads(item) for item in items]

    async def retry_dead_letter(self, index: int) -> bool:
        """Manually retry a dead letter item (admin action)."""
        item = await self.redis.lindex("webhook:dead_letter", index)
        if not item:
            return False
        data = json.loads(item)
        await self.queue_retry(
            data["webhook_id"], data["event_type"], data["payload"], 0
        )
        await self.redis.lrem("webhook:dead_letter", 1, item)
        return True
