"""Tests for SecurityHeadersMiddleware."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def anon_client() -> AsyncClient:
    """Unauthenticated client — sufficient for checking response headers."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_x_content_type_options(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_frame_options(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        assert response.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_xss_protection(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_csp_header_present(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_referrer_policy(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        assert (
            response.headers.get("referrer-policy")
            == "strict-origin-when-cross-origin"
        )

    @pytest.mark.asyncio
    async def test_permissions_policy(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        pp = response.headers.get("permissions-policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp

    @pytest.mark.asyncio
    async def test_server_header_absent(self, anon_client: AsyncClient):
        response = await anon_client.get("/health")
        assert "server" not in response.headers
