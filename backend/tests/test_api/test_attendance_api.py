"""Attendance endpoint tests."""

import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceLog
from app.models.student import Student


@pytest.mark.asyncio
async def test_list_attendance(client: AsyncClient) -> None:
    """Test GET /attendance returns paginated list."""
    response = await client.get("/api/v1/attendance")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data


@pytest.mark.asyncio
async def test_today_attendance(client: AsyncClient) -> None:
    """Test GET /attendance/today returns today's records."""
    response = await client.get("/api/v1/attendance/today")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_attendance_stats(client: AsyncClient) -> None:
    """Test GET /attendance/stats returns statistics."""
    response = await client.get("/api/v1/attendance/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_students" in data["data"]
    assert "present_today" in data["data"]
    assert "absent_today" in data["data"]
    assert "attendance_percentage" in data["data"]


@pytest.mark.asyncio
async def test_weekly_stats(client: AsyncClient) -> None:
    """Test GET /attendance/weekly returns 7 days of stats."""
    response = await client.get("/api/v1/attendance/weekly")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 7


@pytest.mark.asyncio
async def test_student_attendance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /attendance/student/{id} returns student history."""
    student = Student(name="AttTest", class_name="7-A", employee_no="ATT001")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    response = await client.get(f"/api/v1/attendance/student/{student.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "student" in data["data"]
    assert "records" in data["data"]
    assert "stats" in data["data"]


@pytest.mark.asyncio
async def test_attendance_with_date_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /attendance with date filter."""
    today = date.today().isoformat()
    response = await client.get(
        f"/api/v1/attendance?date_from={today}&date_to={today}"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_attendance_report_xlsx(client: AsyncClient) -> None:
    """Test GET /attendance/report returns xlsx."""
    today = date.today().isoformat()
    response = await client.get(
        f"/api/v1/attendance/report?date_from={today}&date_to={today}"
    )
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers.get("content-type", "")
