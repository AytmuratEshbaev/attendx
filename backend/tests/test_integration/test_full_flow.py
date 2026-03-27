"""Integration tests: end-to-end flows across multiple API layers."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


# ---------------------------------------------------------------------------
# Test: Full student creation → attendance recording flow
# ---------------------------------------------------------------------------


class TestStudentAttendanceFlow:
    @pytest.mark.asyncio
    async def test_create_student_then_list(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Create a student via API and verify they appear in the list."""
        payload = {
            "name": "Integration Student",
            "class_name": "10-A",
            "employee_no": "INT001",
            "external_id": "EXTINT001",
        }
        create_resp = await client.post("/api/v1/students", json=payload)
        assert create_resp.status_code == 201
        student_id = create_resp.json()["data"]["id"]

        list_resp = await client.get("/api/v1/students")
        assert list_resp.status_code == 200
        ids = [s["id"] for s in list_resp.json()["data"]]
        assert student_id in ids

    @pytest.mark.asyncio
    async def test_student_full_crud(
        self,
        client: AsyncClient,
    ):
        """Create → Read → Update → Delete lifecycle."""
        # Create
        resp = await client.post(
            "/api/v1/students",
            json={"name": "CRUD Student", "class_name": "11-B", "employee_no": "CRD001"},
        )
        assert resp.status_code == 201
        sid = resp.json()["data"]["id"]

        # Read
        resp = await client.get(f"/api/v1/students/{sid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "CRUD Student"

        # Update
        resp = await client.put(f"/api/v1/students/{sid}", json={"class_name": "12-A"})
        assert resp.status_code == 200
        assert resp.json()["data"]["class_name"] == "12-A"

        # Delete (soft-delete returns 200 with message)
        resp = await client.delete(f"/api/v1/students/{sid}")
        assert resp.status_code == 200

        # Verify soft-deleted: record still retrievable but is_active=False
        resp = await client.get(f"/api/v1/students/{sid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False


class TestWebhookRegistrationFlow:
    @pytest.mark.asyncio
    async def test_create_and_test_webhook(
        self,
        client: AsyncClient,
    ):
        """Create a webhook via API then verify it appears in the list."""
        payload = {
            "url": "https://example.com/hook",
            "events": ["attendance.entry"],
            "description": "Integration test webhook",
        }
        resp = await client.post("/api/v1/webhooks", json=payload)
        assert resp.status_code == 201
        wid = resp.json()["data"]["id"]
        assert resp.json()["data"]["is_active"] is True

        # List webhooks — response is SuccessResponse[list[WebhookResponse]]
        list_resp = await client.get("/api/v1/webhooks")
        assert list_resp.status_code == 200
        ids = [w["id"] for w in list_resp.json()["data"]]
        assert wid in ids


class TestHealthEndpointFlow:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, anon_client: AsyncClient):
        resp = await anon_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ("ok", "healthy", "degraded")

    @pytest.mark.asyncio
    async def test_security_headers_present(self, anon_client: AsyncClient):
        resp = await anon_client.get("/health")
        assert "x-content-type-options" in resp.headers
        assert "x-frame-options" in resp.headers


class TestAuthenticationFlow:
    @pytest.mark.asyncio
    async def test_login_and_access_protected(
        self,
        db_anon_client: AsyncClient,
        sample_user: User,
    ):
        """Login with credentials and use token to access a protected endpoint."""
        resp = await db_anon_client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "testpass123"},
        )
        assert resp.status_code == 200
        token = resp.json()["data"]["access_token"]
        assert token

        me_resp = await db_anon_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["username"] == "testadmin"

    @pytest.mark.asyncio
    async def test_invalid_login_rejected(self, anon_client: AsyncClient):
        resp = await anon_client.post(
            "/api/v1/auth/login",
            json={"username": "testadmin", "password": "wrongpassword"},
        )
        assert resp.status_code in (400, 401, 422)
