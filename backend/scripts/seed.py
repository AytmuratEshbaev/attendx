"""Seed script to populate the database with initial data.

Usage: cd backend && python -m scripts.seed
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.security import encrypt_device_password, generate_api_key, hash_password
from app.models import Base
from app.models.api_key import APIKey
from app.models.device import Device
from app.models.student import Student
from app.models.user import User


async def seed() -> None:
    """Create tables and seed initial data."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    async with AsyncSessionLocal() as session:
        await _seed_users(session)
        await _seed_students(session)
        await _seed_device(session)
        await _seed_api_key(session)
        await session.commit()
    print("Seed data inserted successfully.")


async def _seed_users(session: AsyncSession) -> None:
    """Create the superadmin and teacher users."""
    from sqlalchemy import select

    result = await session.execute(
        select(User).where(User.username == "admin")
    )
    if result.scalar_one_or_none():
        print("  - Superadmin already exists, skipping.")
    else:
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@attendx.local",
            password_hash=hash_password("admin123"),
            role="super_admin",
            is_active=True,
        )
        session.add(admin)
        await session.flush()
        print("  - Superadmin user created (admin / admin123)")

    result = await session.execute(
        select(User).where(User.username == "teacher")
    )
    if result.scalar_one_or_none():
        print("  - Teacher already exists, skipping.")
    else:
        teacher = User(
            id=uuid.uuid4(),
            username="teacher",
            email="teacher@attendx.local",
            password_hash=hash_password("teacher123"),
            role="teacher",
            is_active=True,
        )
        session.add(teacher)
        await session.flush()
        print("  - Teacher user created (teacher / teacher123)")


async def _seed_students(session: AsyncSession) -> None:
    """Create 5 sample students in classes 5-A and 6-B."""
    from sqlalchemy import select

    result = await session.execute(select(Student).limit(1))
    if result.scalar_one_or_none():
        print("  - Students already exist, skipping.")
        return

    students_data = [
        {"name": "Alisher Karimov", "class_name": "5-A", "employee_no": "EMP001", "parent_phone": "+998901234501"},
        {"name": "Dilnoza Rahimova", "class_name": "5-A", "employee_no": "EMP002", "parent_phone": "+998901234502"},
        {"name": "Sardor Toshmatov", "class_name": "5-A", "employee_no": "EMP003", "parent_phone": "+998901234503"},
        {"name": "Malika Usmanova", "class_name": "6-B", "employee_no": "EMP004", "parent_phone": "+998901234504"},
        {"name": "Jasur Abdullaev", "class_name": "6-B", "employee_no": "EMP005", "parent_phone": "+998901234505"},
    ]
    for data in students_data:
        session.add(Student(**data))
    await session.flush()
    print(f"  - {len(students_data)} sample students created.")


async def _seed_device(session: AsyncSession) -> None:
    """Create a sample device."""
    from sqlalchemy import select

    result = await session.execute(select(Device).limit(1))
    if result.scalar_one_or_none():
        print("  - Device already exists, skipping.")
        return

    device = Device(
        name="Main Entrance",
        ip_address="192.168.1.100",
        port=80,
        username="admin",
        password_enc=encrypt_device_password("admin123"),
        is_entry=True,
        is_active=True,
    )
    session.add(device)
    await session.flush()
    print("  - Sample device created (Main Entrance @ 192.168.1.100)")


async def _seed_api_key(session: AsyncSession) -> None:
    """Create a default API key."""
    from sqlalchemy import select

    result = await session.execute(select(APIKey).limit(1))
    if result.scalar_one_or_none():
        print("  - API key already exists, skipping.")
        return

    raw_key, hashed_key = generate_api_key()
    api_key = APIKey(
        name="Default API Key",
        key_hash=hashed_key,
        is_active=True,
        permissions={"all": True},
    )
    session.add(api_key)
    await session.flush()
    print(f"  - Default API key created: {raw_key}")


if __name__ == "__main__":
    asyncio.run(seed())
