"""AccessGroups API tests — group CRUD with device/student management."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_group import AccessGroupStudent
from app.models.device import Device
from app.models.student import Student

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GROUP_PAYLOAD = {
    "name": "1-sinf kirish guruhi",
    "description": "Birinchi sinf o'quvchilari",
}


async def _create_group(client: AsyncClient, payload: dict | None = None) -> dict:
    resp = await client.post(
        "/api/v1/access-groups", json=payload or GROUP_PAYLOAD
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/access-groups", json=GROUP_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "1-sinf kirish guruhi"
    assert data["timetable_id"] is None
    assert data["devices"] == []
    assert data["students"] == []


@pytest.mark.asyncio
async def test_create_group_duplicate_name(client: AsyncClient) -> None:
    await _create_group(client)
    resp = await client.post("/api/v1/access-groups", json=GROUP_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_group_teacher_forbidden(teacher_client: AsyncClient) -> None:
    resp = await teacher_client.post("/api/v1/access-groups", json=GROUP_PAYLOAD)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_group_with_timetable(client: AsyncClient) -> None:
    """Create a group with an attached timetable."""
    tt_resp = await client.post(
        "/api/v1/timetables",
        json={
            "timetable_type": "recurring",
            "name": "Du-Ju 08-17",
            "weekdays": ["Monday", "Friday"],
            "start_time": "08:00:00",
            "end_time": "17:00:00",
        },
    )
    assert tt_resp.status_code == 201
    tt_id = tt_resp.json()["data"]["id"]

    resp = await client.post(
        "/api/v1/access-groups",
        json={"name": "Guruh jadval bilan", "timetable_id": tt_id},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["timetable_id"] == tt_id
    assert data["timetable"]["name"] == "Du-Ju 08-17"


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_groups_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/access-groups")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_list_groups_returns_all(client: AsyncClient) -> None:
    await _create_group(client, {"name": "Guruh A"})
    await _create_group(client, {"name": "Guruh B"})
    resp = await client.get("/api/v1/access-groups")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_group(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.get(f"/api/v1/access-groups/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == created["name"]


@pytest.mark.asyncio
async def test_get_group_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/access-groups/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_group_name(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.put(
        f"/api/v1/access-groups/{created['id']}",
        json={"name": "Yangilangan guruh"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Yangilangan guruh"


@pytest.mark.asyncio
async def test_update_group_not_found(client: AsyncClient) -> None:
    resp = await client.put("/api/v1/access-groups/99999", json={"name": "X"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.delete(f"/api/v1/access-groups/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "AccessGroup deleted"

    resp = await client.get(f"/api/v1/access-groups/{created['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_group_not_found(client: AsyncClient) -> None:
    resp = await client.delete("/api/v1/access-groups/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DEVICE management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_device_to_group(
    client: AsyncClient, sample_device: Device
) -> None:
    created = await _create_group(client)
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/devices/{sample_device.id}"
    )
    assert resp.status_code == 200
    devices = resp.json()["data"]["devices"]
    assert any(d["id"] == sample_device.id for d in devices)


@pytest.mark.asyncio
async def test_add_device_idempotent(
    client: AsyncClient, sample_device: Device
) -> None:
    created = await _create_group(client)
    await client.post(
        f"/api/v1/access-groups/{created['id']}/devices/{sample_device.id}"
    )
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/devices/{sample_device.id}"
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]["devices"]) == 1


@pytest.mark.asyncio
async def test_add_device_not_found(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/devices/99999"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_remove_device_from_group(
    client: AsyncClient, sample_device: Device
) -> None:
    created = await _create_group(client)
    await client.post(
        f"/api/v1/access-groups/{created['id']}/devices/{sample_device.id}"
    )
    resp = await client.delete(
        f"/api/v1/access-groups/{created['id']}/devices/{sample_device.id}"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["devices"] == []


# ---------------------------------------------------------------------------
# STUDENT management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_student_to_group(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert str(data["student_id"]) == str(student.id)
    assert data["sync_status"] == "pending"


@pytest.mark.asyncio
async def test_add_student_duplicate(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_add_student_not_found(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{uuid.uuid4()}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_remove_student_from_group(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    resp = await client.delete(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["message"] == "Student removed from access group"


@pytest.mark.asyncio
async def test_remove_student_not_member(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    resp = await client.delete(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_group_students_shown_in_detail(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[2]
    await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    resp = await client.get(f"/api/v1/access-groups/{created['id']}")
    assert resp.status_code == 200
    students = resp.json()["data"]["students"]
    assert len(students) == 1
    assert students[0]["student"]["name"] == student.name


# ---------------------------------------------------------------------------
# STUDENT RETRY SYNC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_student_sync(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}"
    )
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}/sync"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sync_status"] == "pending"


@pytest.mark.asyncio
async def test_retry_student_sync_not_member(
    client: AsyncClient,
    sample_students: list[Student],
) -> None:
    created = await _create_group(client)
    student = sample_students[0]
    resp = await client.post(
        f"/api/v1/access-groups/{created['id']}/students/{student.id}/sync"
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# SYNC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_group_no_students(client: AsyncClient) -> None:
    created = await _create_group(client)
    resp = await client.post(f"/api/v1/access-groups/{created['id']}/sync")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["synced"] == 0
    assert data["devices"] == 0


@pytest.mark.asyncio
async def test_sync_group_with_students(
    client: AsyncClient,
    sample_students: list[Student],
    sample_device: Device,
) -> None:
    created = await _create_group(client)
    group_id = created["id"]

    await client.post(
        f"/api/v1/access-groups/{group_id}/devices/{sample_device.id}"
    )
    for s in sample_students[:3]:
        await client.post(
            f"/api/v1/access-groups/{group_id}/students/{s.id}"
        )

    resp = await client.post(f"/api/v1/access-groups/{group_id}/sync")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["synced"] == 3
    assert data["devices"] == 1


@pytest.mark.asyncio
async def test_sync_group_not_found(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/access-groups/99999/sync")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cascade delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_group_cascades_students(
    client: AsyncClient,
    sample_students: list[Student],
    db_session: AsyncSession,
) -> None:
    created = await _create_group(client)
    group_id = created["id"]
    for s in sample_students[:2]:
        await client.post(
            f"/api/v1/access-groups/{group_id}/students/{s.id}"
        )

    await client.delete(f"/api/v1/access-groups/{group_id}")

    result = await db_session.execute(
        select(AccessGroupStudent).where(
            AccessGroupStudent.access_group_id == group_id
        )
    )
    assert result.scalars().all() == []
