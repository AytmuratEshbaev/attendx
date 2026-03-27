"""Enhanced brute-force protection with tiered lockout levels."""

import structlog

logger = structlog.get_logger()

_TIERS = [
    # (min_attempts, lockout_seconds, level)
    (20, 86_400, "critical"),   # 24 hours
    (10, 3_600, "high"),        # 1 hour
    (5, 900, "medium"),         # 15 minutes
]
_DEFAULT_TTL = 900  # reset counter after 15 min of inactivity


class BruteForceProtection:
    """
    Tiered brute-force protection backed by Redis.

    Key pattern: ``bruteforce:login:{identifier}``
    where identifier is a username or ``ip:{address}``.
    """

    def __init__(self, redis) -> None:
        self.redis = redis

    def _key(self, identifier: str) -> str:
        return f"bruteforce:login:{identifier}"

    async def check_login_attempt(self, identifier: str) -> dict:
        """
        Return whether a login attempt is allowed for *identifier*.

        Response keys:
        - ``allowed`` (bool)
        - ``remaining_attempts`` (int, before lockout)
        - ``locked_until`` (str | None, e.g. "300s")
        - ``lockout_level`` (str | None)
        """
        key = self._key(identifier)
        raw = await self.redis.get(key)
        attempts = int(raw) if raw else 0

        for min_attempts, _lockout_secs, level in _TIERS:
            if attempts >= min_attempts:
                ttl = await self.redis.ttl(key)
                if ttl > 0:
                    return {
                        "allowed": False,
                        "remaining_attempts": 0,
                        "locked_until": f"{ttl}s",
                        "lockout_level": level,
                    }

        remaining = max(5 - attempts, 0)
        return {
            "allowed": True,
            "remaining_attempts": remaining,
            "locked_until": None,
            "lockout_level": None,
        }

    async def record_failed_attempt(self, identifier: str) -> None:
        """Increment the failed-attempt counter and apply the correct TTL."""
        key = self._key(identifier)
        attempts = await self.redis.incr(key)

        for min_attempts, lockout_secs, _level in _TIERS:
            if attempts >= min_attempts:
                await self.redis.expire(key, lockout_secs)
                return

        # Below first tier — use default TTL to auto-expire inactivity counter
        await self.redis.expire(key, _DEFAULT_TTL)

    async def record_successful_login(self, identifier: str) -> None:
        """Reset failed-attempt counter on successful authentication."""
        await self.redis.delete(self._key(identifier))

    async def check_api_rate_limit(
        self, api_key: str, max_per_minute: int = 100
    ) -> dict:
        """Sliding-window rate limit per API key (per minute)."""
        key = f"ratelimit:api:{api_key}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)

        ttl = await self.redis.ttl(key)
        remaining = max(max_per_minute - current, 0)
        return {
            "allowed": current <= max_per_minute,
            "remaining": remaining,
            "reset_in": ttl,
        }

    async def get_blocked_identifiers(self) -> list[dict]:
        """Return all identifiers that have ≥ 5 failed attempts (admin view)."""
        keys = await self.redis.keys("bruteforce:login:*")
        blocked = []
        for key in keys:
            raw = await self.redis.get(key)
            if not raw:
                continue
            attempts = int(raw)
            if attempts >= 5:
                ttl = await self.redis.ttl(key)
                identifier = key.replace("bruteforce:login:", "")
                blocked.append(
                    {
                        "identifier": identifier,
                        "attempts": attempts,
                        "locked_for_seconds": ttl,
                    }
                )
        return blocked
