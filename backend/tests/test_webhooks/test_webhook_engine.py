"""Tests for webhook delivery engine."""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from app.services.webhook_engine import WebhookEngine


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.zadd = AsyncMock()
    redis.zrangebyscore = AsyncMock(return_value=[])
    redis.zcard = AsyncMock(return_value=0)
    redis.llen = AsyncMock(return_value=0)
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    return redis


@pytest.fixture
def mock_webhook():
    """Create a mock webhook object."""
    wh = MagicMock()
    wh.id = uuid.uuid4()
    wh.url = "https://example.com/webhook"
    wh.secret = "test-secret-key"
    wh.events = ["student.created", "attendance.entry"]
    wh.is_active = True
    return wh


class TestGenerateSignature:
    def test_produces_valid_hmac(self):
        secret = "my-secret"
        payload = '{"event": "test"}'
        result = WebhookEngine._generate_signature(secret, payload)

        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert result == expected

    def test_different_secrets_produce_different_signatures(self):
        payload = '{"event": "test"}'
        sig1 = WebhookEngine._generate_signature("secret1", payload)
        sig2 = WebhookEngine._generate_signature("secret2", payload)
        assert sig1 != sig2

    def test_different_payloads_produce_different_signatures(self):
        secret = "my-secret"
        sig1 = WebhookEngine._generate_signature(secret, '{"a": 1}')
        sig2 = WebhookEngine._generate_signature(secret, '{"a": 2}')
        assert sig1 != sig2


class TestVerifySignature:
    def test_valid_signature_returns_true(self):
        secret = "my-secret"
        payload = '{"event": "test"}'
        sig = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        assert WebhookEngine.verify_signature(
            secret, payload, f"sha256={sig}"
        )

    def test_invalid_signature_returns_false(self):
        assert not WebhookEngine.verify_signature(
            "secret", '{"event": "test"}', "sha256=invalid"
        )

    def test_wrong_secret_returns_false(self):
        payload = '{"event": "test"}'
        sig = hmac.new(
            b"correct-secret", payload.encode(), hashlib.sha256
        ).hexdigest()
        assert not WebhookEngine.verify_signature(
            "wrong-secret", payload, f"sha256={sig}"
        )


class TestDeliver:
    @pytest.mark.asyncio
    async def test_successful_delivery(self, mock_redis, mock_webhook):
        engine = WebhookEngine(AsyncMock(), mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        engine.http_client = mock_client

        result = await engine.deliver(
            mock_webhook, "student.created", {"name": "Test"}
        )

        assert result.success is True
        assert result.status_code == 200
        assert result.event_type == "student.created"
        assert result.webhook_id == mock_webhook.id

        # Verify headers
        call_args = mock_client.post.call_args
        headers = call_args.kwargs["headers"]
        assert headers["X-AttendX-Event"] == "student.created"
        assert headers["X-AttendX-Signature"].startswith("sha256=")
        assert headers["User-Agent"] == "AttendX-Webhook/1.0"

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_redis, mock_webhook):
        engine = WebhookEngine(AsyncMock(), mock_redis)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )
        engine.http_client = mock_client

        result = await engine.deliver(
            mock_webhook, "student.created", {"name": "Test"}
        )

        assert result.success is False
        assert result.status_code == 0
        assert result.error == "Connection timeout"

    @pytest.mark.asyncio
    async def test_connection_error_handling(
        self, mock_redis, mock_webhook
    ):
        engine = WebhookEngine(AsyncMock(), mock_redis)

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("refused")
        )
        engine.http_client = mock_client

        result = await engine.deliver(
            mock_webhook, "student.created", {"name": "Test"}
        )

        assert result.success is False
        assert result.status_code == 0
        assert "Connection error" in result.error

    @pytest.mark.asyncio
    async def test_non_2xx_is_failure(self, mock_redis, mock_webhook):
        engine = WebhookEngine(AsyncMock(), mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        engine.http_client = mock_client

        result = await engine.deliver(
            mock_webhook, "student.created", {"name": "Test"}
        )

        assert result.success is False
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_payload_size_limit(self, mock_redis, mock_webhook):
        engine = WebhookEngine(AsyncMock(), mock_redis)
        engine.http_client = AsyncMock()

        # Create oversized payload
        huge_payload = {"data": "x" * (256 * 1024 + 1000)}

        result = await engine.deliver(
            mock_webhook, "student.created", huge_payload
        )

        assert result.success is False
        assert "Payload exceeds" in result.error

    @pytest.mark.asyncio
    async def test_correct_hmac_signature_in_headers(
        self, mock_redis, mock_webhook
    ):
        engine = WebhookEngine(AsyncMock(), mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        engine.http_client = mock_client

        await engine.deliver(
            mock_webhook, "student.created", {"name": "Test"}
        )

        call_args = mock_client.post.call_args
        payload_json = call_args.kwargs["content"]
        sig_header = call_args.kwargs["headers"]["X-AttendX-Signature"]

        # Verify the signature matches
        assert WebhookEngine.verify_signature(
            mock_webhook.secret, payload_json, sig_header
        )


class TestDispatchEvent:
    @pytest.mark.asyncio
    async def test_dispatches_to_subscribed_webhooks(self, mock_redis):
        mock_webhook = MagicMock()
        mock_webhook.id = uuid.uuid4()
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = "secret"
        mock_webhook.events = ["student.created"]
        mock_webhook.is_active = True

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        # Use a proper async context manager
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def fake_session_factory():
            yield mock_session

        engine = WebhookEngine(fake_session_factory, mock_redis)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        engine.http_client = mock_client

        results = await engine.dispatch_event(
            "student.created", {"name": "Test"}
        )

        assert results["total"] == 1
        assert results["delivered"] == 1
        assert results["failed"] == 0

    @pytest.mark.asyncio
    async def test_skips_unsubscribed_webhooks(self, mock_redis):
        mock_webhook = MagicMock()
        mock_webhook.id = uuid.uuid4()
        mock_webhook.url = "https://example.com/hook"
        mock_webhook.secret = "secret"
        mock_webhook.events = ["attendance.entry"]  # Not subscribed to student.created
        mock_webhook.is_active = True

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def fake_session_factory():
            yield mock_session

        engine = WebhookEngine(fake_session_factory, mock_redis)
        engine.http_client = AsyncMock()

        results = await engine.dispatch_event(
            "student.created", {"name": "Test"}
        )

        assert results["total"] == 0
