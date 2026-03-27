"""Circuit breaker pattern for webhook endpoints."""

from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


class CircuitBreaker:
    """
    Circuit breaker pattern for webhook endpoints.

    States:
    - CLOSED: Normal operation, deliveries proceed
    - OPEN: Too many failures, deliveries skipped (fast-fail)
    - HALF_OPEN: Testing if endpoint recovered

    Thresholds:
    - Open after 5 consecutive failures
    - Stay open for 60 seconds
    - Half-open: allow 1 test request
    - If test succeeds -> CLOSED
    - If test fails -> OPEN again (reset timer)
    """

    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60  # seconds
    REDIS_PREFIX = "webhook:circuit:"

    def __init__(self, redis_client):
        self.redis = redis_client

    async def can_deliver(self, webhook_id: str) -> bool:
        """Check if delivery is allowed for this webhook."""
        state = await self._get_state(webhook_id)

        if state == "closed":
            return True
        elif state == "open":
            opened_at = await self.redis.get(
                f"{self.REDIS_PREFIX}{webhook_id}:opened_at"
            )
            if opened_at:
                elapsed = (
                    datetime.now(timezone.utc).timestamp() - float(opened_at)
                )
                if elapsed >= self.RECOVERY_TIMEOUT:
                    await self._set_state(webhook_id, "half_open")
                    return True  # Allow one test request
            return False
        elif state == "half_open":
            return True  # Allow test request

        return True  # Default: allow

    async def record_success(self, webhook_id: str) -> None:
        """Record successful delivery."""
        state = await self._get_state(webhook_id)

        if state == "half_open":
            await self._set_state(webhook_id, "closed")
            await self.redis.delete(
                f"{self.REDIS_PREFIX}{webhook_id}:failures"
            )
            logger.info(
                "circuit_breaker_closed", webhook_id=webhook_id
            )

        # Reset failure counter on success
        await self.redis.delete(f"{self.REDIS_PREFIX}{webhook_id}:failures")

    async def record_failure(self, webhook_id: str) -> None:
        """Record failed delivery."""
        state = await self._get_state(webhook_id)

        if state == "half_open":
            await self._set_state(webhook_id, "open")
            await self.redis.set(
                f"{self.REDIS_PREFIX}{webhook_id}:opened_at",
                str(datetime.now(timezone.utc).timestamp()),
            )
            logger.warning(
                "circuit_breaker_reopened", webhook_id=webhook_id
            )
            return

        failures = await self.redis.incr(
            f"{self.REDIS_PREFIX}{webhook_id}:failures"
        )

        if failures >= self.FAILURE_THRESHOLD:
            await self._set_state(webhook_id, "open")
            await self.redis.set(
                f"{self.REDIS_PREFIX}{webhook_id}:opened_at",
                str(datetime.now(timezone.utc).timestamp()),
            )
            logger.warning(
                "circuit_breaker_opened",
                webhook_id=webhook_id,
                consecutive_failures=failures,
            )

    async def get_status(self, webhook_id: str) -> dict:
        """Get circuit breaker status for a webhook."""
        state = await self._get_state(webhook_id)
        failures = await self.redis.get(
            f"{self.REDIS_PREFIX}{webhook_id}:failures"
        )
        opened_at = await self.redis.get(
            f"{self.REDIS_PREFIX}{webhook_id}:opened_at"
        )

        return {
            "webhook_id": webhook_id,
            "state": state,
            "consecutive_failures": int(failures) if failures else 0,
            "opened_at": opened_at if opened_at else None,
            "recovery_timeout_seconds": self.RECOVERY_TIMEOUT,
        }

    async def reset(self, webhook_id: str) -> None:
        """Manually reset circuit breaker (admin action)."""
        await self._set_state(webhook_id, "closed")
        await self.redis.delete(
            f"{self.REDIS_PREFIX}{webhook_id}:failures"
        )
        await self.redis.delete(
            f"{self.REDIS_PREFIX}{webhook_id}:opened_at"
        )

    async def _get_state(self, webhook_id: str) -> str:
        state = await self.redis.get(
            f"{self.REDIS_PREFIX}{webhook_id}:state"
        )
        if isinstance(state, bytes):
            state = state.decode()
        return state if state else "closed"

    async def _set_state(self, webhook_id: str, state: str) -> None:
        await self.redis.set(
            f"{self.REDIS_PREFIX}{webhook_id}:state", state
        )
