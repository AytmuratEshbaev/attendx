"""Timetables API tests — recurring and one-time access schedules."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.student import Student


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RECURRING_PAYLOAD = {
    "timetable_type": "recurring",
    "name": "Maktab dars vaqti",
    "description": "Haftalik dars jadvali",
    "weekdays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "start_time": "08:00:00",
    "end_time": "16:00:00",
}

ONE_TIME_PAYLOAD = {
    "timetable_type": "one_time",
    "name": "Kuzgi imtihon",
    "description": "Bir martalik imtihon",
    "date_from": "2026-01-15",
    "date_to": "2026-01-30",
    "ot_start_time": "09:00:00",
    "ot_end_time": "12:00:00",
}


async def _create_timetable(client: AsyncClient, payload: dict) -> dict:
    resp = await client.post("/api/v1/timetables", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_recurring_timetable(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/timetables", json=RECURRING_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["timetable_type"] == "recurring"
    assert data["name"] == "Maktab dars vaqti"
    assert "Monday" in data["weekdays"]
    assert data["start_time"] == "08:00:00"
    assert data["end_time"] == "16:00:00"
    assert data["date_from"] is None


@pytest.mark.asyncio
async def test_create_one_time_timetable(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/timetables", json=ONE_TIME_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["timetable_type"] == "one_time"
    assert data["name"] == "Kuzgi imtihon"
    assert data["date_from"] == "2026-01-15"
    assert data["date_to"] == "2026-01-30"
    assert data["ot_start_time"] == "09:00:00"
    assert data["weekdays"] is None


@pytest.mark.asyncio
async def test_create_timetable_duplicate_name(client: AsyncClient) -> None:
    await _create_timetable(client, RECURRING_PAYLOAD)
    resp = await client.post("/api/v1/timetables", json=RECURRING_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_timetable_missing_required_fields(client: AsyncClient) -> None:
    """timetable_type=recurring without weekdays → validation error."""
    resp = await client.post(
        "/api/v1/timetables",
        json={
            "timetable_type": "recurring",
            "name": "Test",
            "start_time": "08:00:00",
            "end_time": "16:00:00",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_timetable_invalid_type(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/timetables",
        json={"timetable_type": "unknown", "name": "Test"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_timetable_teacher_forbidden(teacher_client: AsyncClient) -> None:
    resp = await teacher_client.post("/api/v1/timetables", json=RECURRING_PAYLOAD)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_timetables_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/timetables")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_list_timetables_returns_all(client: AsyncClient) -> None:
    await _create_timetable(client, RECURRING_PAYLOAD)
    await _create_timetable(client, ONE_TIME_PAYLOAD)
    resp = await client.get("/api/v1/timetables")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


@pytest.mark.asyncio
async def test_list_timetables_filter_by_type(client: AsyncClient) -> None:
    await _create_timetable(client, RECURRING_PAYLOAD)
    await _create_timetable(client, ONE_TIME_PAYLOAD)

    resp = await client.get("/api/v1/timetables?timetable_type=recurring")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["timetable_type"] == "recurring"

    resp = await client.get("/api/v1/timetables?timetable_type=one_time")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["timetable_type"] == "one_time"


@pytest.mark.asyncio
async def test_list_timetables_invalid_filter(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/timetables?timetable_type=wrong")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_timetable(client: AsyncClient) -> None:
    created = await _create_timetable(client, RECURRING_PAYLOAD)
    resp = await client.get(f"/api/v1/timetables/{created['id']}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == created["id"]
    assert data["name"] == "Maktab dars vaqti"


@pytest.mark.asyncio
async def test_get_timetable_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/timetables/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_timetable_name(client: AsyncClient) -> None:
    created = await _create_timetable(client, RECURRING_PAYLOAD)
    resp = await client.put(
        f"/api/v1/timetables/{created['id']}",
        json={"name": "Yangilangan nom"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Yangilangan nom"


@pytest.mark.asyncio
async def test_update_timetable_weekdays(client: AsyncClient) -> None:
    created = await _create_timetable(client, RECURRING_PAYLOAD)
    resp = await client.put(
        f"/api/v1/timetables/{created['id']}",
        json={"weekdays": ["Monday", "Wednesday", "Friday"]},
    )
    assert resp.status_code == 200
    weekdays = resp.json()["data"]["weekdays"]
    assert sorted(weekdays) == ["Friday", "Monday", "Wednesday"]


@pytest.mark.asyncio
async def test_update_timetable_not_found(client: AsyncClient) -> None:
    resp = await client.put("/api/v1/timetables/99999", json={"name": "X"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_timetable(client: AsyncClient) -> None:
    created = await _create_timetable(client, RECURRING_PAYLOAD)
    resp = await client.delete(f"/api/v1/timetables/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "Timetable deleted"

    resp = await client.get(f"/api/v1/timetables/{created['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_timetable_not_found(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/timetables/99999")
    assert resp.status_code == 404
