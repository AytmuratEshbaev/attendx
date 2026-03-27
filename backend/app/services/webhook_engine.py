"""Production-ready webhook delivery engine."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.models.webhook_log import WebhookLog
from app.schemas.webhook_delivery import WebhookDeliveryResult
from app.services.webhook_circuit_breaker import CircuitBreaker

logger = structlog.get_logger()


class WebhookEngine:
    """
    Production-ready webhook delivery engine.

    Features: HMAC signing, async delivery, retry with exponential backoff,
    circuit breaker, delivery logging, batch processing.
    """

    RETRY_DELAYS = [10, 60, 300]  # seconds: 10s, 1min, 5min
    DELIVERY_TIMEOUT = 30  # seconds
    MAX_PAYLOAD_SIZE = 256 * 1024  # 256KB max payload

    def __init__(self, db_session_factory, redis_client):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.http_client: httpx.AsyncClient | None = None
        self.circuit_breaker = CircuitBreaker(redis_client)
        self._retry_manager = None  # Set after initialization to avoid circular

    async def initialize(self) -> None:
        """Create shared HTTP client for all webhook deliveries."""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=self.DELIVERY_TIMEOUT,
                write=10.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=50, max_keepalive_connections=10
            ),
            follow_redirects=False,
            verify=True,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()

    def set_retry_manager(self, retry_manager) -> None:
        """Set the retry manager (called after both are initialized)."""
        self._retry_manager = retry_manager

    async def dispatch_event(
        self, event_type: str, payload: dict
    ) -> dict:
        """
        Main entry point: dispatch an event to all subscribed webhooks.

        Returns:
            {total, delivered, failed, skipped, details}
        """
        results = {
            "total": 0,
            "delivered": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        async with self.db_session_factory() as session:
            # Query all active webhooks
            stmt = select(Webhook).where(Webhook.is_active.is_(True))
            result = await session.execute(stmt)
            webhooks = result.scalars().all()

            for webhook in webhooks:
                # Check if webhook is subscribed to this event
                events = webhook.events
                if isinstance(events, list):
                    if event_type not in events:
                        continue
                elif isinstance(events, dict):
                    if event_type not in events.get("events", []):
                        continue

                results["total"] += 1
                wh_id = str(webhook.id)

                # Check circuit breaker
                if not await self.circuit_breaker.can_deliver(wh_id):
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "webhook_id": wh_id,
                            "status": "skipped",
                            "reason": "circuit_breaker_open",
                        }
                    )
                    logger.info(
                        "webhook_skipped_circuit_open",
                        webhook_id=wh_id,
                        event_type=event_type,
                    )
                    continue

                # Attempt delivery
                delivery_result = await self.deliver(
                    webhook, event_type, payload
                )

                # Log the result
                await self._log_delivery(session, delivery_result)

                if delivery_result.success:
                    results["delivered"] += 1
                    await self.circuit_breaker.record_success(wh_id)
                    results["details"].append(
                        {
                            "webhook_id": wh_id,
                            "status": "delivered",
                            "status_code": delivery_result.status_code,
                            "duration_ms": delivery_result.duration_ms,
                        }
                    )
                else:
                    results["failed"] += 1
                    await self.circuit_breaker.record_failure(wh_id)
                    results["details"].append(
                        {
                            "webhook_id": wh_id,
                            "status": "failed",
                            "error": delivery_result.error
                            or f"HTTP {delivery_result.status_code}",
                        }
                    )
                    # Queue for retry
                    if self._retry_manager:
                        await self._retry_manager.queue_retry(
                            wh_id, event_type, payload, 1
                        )

            await session.commit()

        logger.info(
            "webhook_dispatch_complete",
            event_type=event_type,
            total=results["total"],
            delivered=results["delivered"],
            failed=results["failed"],
            skipped=results["skipped"],
        )
        return results

    async def deliver(
        self, webhook, event_type: str, payload: dict
    ) -> WebhookDeliveryResult:
        """Deliver a single webhook with full lifecycle."""
        delivery_id = str(uuid4())

        full_payload = {
            "event": event_type,
            "delivery_id": delivery_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }

        payload_json = json.dumps(
            full_payload, default=str, ensure_ascii=False
        )

        # Check payload size
        if len(payload_json.encode()) > self.MAX_PAYLOAD_SIZE:
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                error="Payload exceeds maximum size limit",
                payload=full_payload,
            )

        # Generate HMAC-SHA256 signature
        signature = self._generate_signature(webhook.secret, payload_json)
        now_ts = str(int(datetime.now(timezone.utc).timestamp()))

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "AttendX-Webhook/1.0",
            "X-AttendX-Event": event_type,
            "X-AttendX-Delivery": delivery_id,
            "X-AttendX-Signature": f"sha256={signature}",
            "X-AttendX-Timestamp": now_ts,
        }

        if not self.http_client:
            await self.initialize()

        start_time = time.monotonic()
        try:
            response = await self.http_client.post(
                str(webhook.url),
                content=payload_json,
                headers=headers,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)
            success = 200 <= response.status_code < 300

            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=success,
                status_code=response.status_code,
                response_body=response.text[:1000],
                duration_ms=duration_ms,
                attempt=1,
                payload=full_payload,
            )
        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                response_body="Timeout",
                duration_ms=duration_ms,
                error="Connection timeout",
                attempt=1,
                payload=full_payload,
            )
        except httpx.ConnectError as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                response_body="",
                duration_ms=duration_ms,
                error=f"Connection error: {str(e)[:200]}",
                attempt=1,
                payload=full_payload,
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                response_body="",
                duration_ms=duration_ms,
                error=f"Unexpected error: {str(e)[:200]}",
                attempt=1,
                payload=full_payload,
            )

    async def _log_delivery(
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

    @staticmethod
    def _generate_signature(secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_signature(
        secret: str, payload: str, signature: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature.

        Receivers should use this logic to verify incoming webhooks.
        """
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
