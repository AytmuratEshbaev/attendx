"""Student endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student


@pytest.mark.asyncio
async def test_create_student(client: AsyncClient) -> None:
    """Test POST /students creates a student."""
    response = await client.post(
        "/api/v1/students",
        json={"name": "Test Student", "class_name": "7-A", "employee_no": "TST001"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Student"
    assert data["data"]["class_name"] == "7-A"
    assert data["data"]["employee_no"] == "TST001"
    assert data["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_create_student_missing_employee_no(client: AsyncClient) -> None:
    """Test POST /students without employee_no returns 422."""
    response = await client.post(
        "/api/v1/students",
        json={"name": "Test Student", "class_name": "7-A"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_students(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /students returns paginated list."""
    for i in range(3):
        db_session.add(
            Student(name=f"Student {i}", class_name="8-A", employee_no=f"LST{i:03d}")
        )
    await db_session.commit()

    response = await client.get("/api/v1/students")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data
    assert data["pagination"]["total"] >= 3


@pytest.mark.asyncio
async def test_list_students_class_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /students?class_name= filters by class."""
    db_session.add(Student(name="A1", class_name="9-A", employee_no="FLT001"))
    db_session.add(Student(name="B1", class_name="9-B", employee_no="FLT002"))
    await db_session.commit()

    response = await client.get("/api/v1/students?class_name=9-A")
    assert response.status_code == 200
    data = response.json()
    assert all(s["class_name"] == "9-A" for s in data["data"])


@pytest.mark.asyncio
async def test_list_students_search(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /students?search= searches by name."""
    db_session.add(Student(name="Alice Johnson", class_name="9-A", employee_no="SRC001"))
    db_session.add(Student(name="Bob Smith", class_name="9-A", employee_no="SRC002"))
    await db_session.commit()

    response = await client.get("/api/v1/students?search=Alice")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any("Alice" in s["name"] for s in data["data"])


@pytest.mark.asyncio
async def test_list_students_pagination(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test pagination parameters work correctly."""
    for i in range(5):
        db_session.add(
            Student(name=f"Page Student {i}", class_name="10-A", employee_no=f"PG{i:03d}")
        )
    await db_session.commit()

    response = await client.get("/api/v1/students?page=1&per_page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2
    assert data["pagination"]["per_page"] == 2


@pytest.mark.asyncio
async def test_get_student(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /students/{id} returns student."""
    student = Student(name="Get Me", class_name="9-A", employee_no="GET001")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    response = await client.get(f"/api/v1/students/{student.id}")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Get Me"


@pytest.mark.asyncio
async def test_get_student_not_found(client: AsyncClient) -> None:
    """Test GET /students/{id} returns 404 for missing student."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/students/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_student(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test PUT /students/{id} updates student."""
    student = Student(name="Old Name", class_name="10-A", employee_no="UPD001")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    response = await client.put(
        f"/api/v1/students/{student.id}",
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_student(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test DELETE /students/{id} soft-deletes."""
    student = Student(name="Delete Me", class_name="11-A", employee_no="DEL001")
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    response = await client.delete(f"/api/v1/students/{student.id}")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Student deactivated"


@pytest.mark.asyncio
async def test_duplicate_external_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test creating student with duplicate external_id returns 409."""
    student = Student(
        name="First", class_name="5-A", external_id="EXT001", employee_no="DUP001"
    )
    db_session.add(student)
    await db_session.commit()

    response = await client.post(
        "/api/v1/students",
        json={
            "name": "Second",
            "class_name": "5-B",
            "external_id": "EXT001",
            "employee_no": "DUP002",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_export_students_xlsx(client: AsyncClient) -> None:
    """Test GET /students/export returns xlsx file."""
    response = await client.get("/api/v1/students/export")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_export_students_csv(client: AsyncClient) -> None:
    """Test GET /students/export?format=csv returns csv file."""
    response = await client.get("/api/v1/students/export?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_crud_full_cycle(
    client: AsyncClient,
) -> None:
    """Test full CRUD cycle: create -> get -> update -> list -> delete."""
    # Create
    resp = await client.post(
        "/api/v1/students",
        json={"name": "Cycle Test", "class_name": "8-A", "employee_no": "CYC001"},
    )
    assert resp.status_code == 201
    student_id = resp.json()["data"]["id"]

    # Get
    resp = await client.get(f"/api/v1/students/{student_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Cycle Test"

    # Update
    resp = await client.put(
        f"/api/v1/students/{student_id}",
        json={"name": "Updated Cycle Test"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Updated Cycle Test"

    # List
    resp = await client.get("/api/v1/students")
    assert resp.status_code == 200
    assert any(s["id"] == student_id for s in resp.json()["data"])

    # Delete
    resp = await client.delete(f"/api/v1/students/{student_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_teacher_cannot_create_student(
    teacher_client: AsyncClient,
) -> None:
    """Test that teacher role cannot create students (requires admin)."""
    response = await teacher_client.post(
        "/api/v1/students",
        json={"name": "Forbidden", "class_name": "7-A", "employee_no": "FORBID001"},
    )
    assert response.status_code == 403
