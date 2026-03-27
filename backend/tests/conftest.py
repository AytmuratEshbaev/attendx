"""Shared pytest fixtures with in-memory SQLite async test database and FakeRedis."""

import asyncio
import fnmatch
import uuid

import pytest_asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.core.security import create_access_token, encrypt_device_password, hash_password
from app.models import Base
from app.models.attendance import AttendanceLog
from app.models.device import Device
from app.models.student import Student
from app.models.user import User
from app.models.webhook import Webhook

# -- Test database engine (SQLite in-memory, shared single connection) ---------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# -- Fake Redis ----------------------------------------------------------------


class FakePipeline:
    """Minimal pipeline mock that executes commands immediately."""

    def __init__(self, redis: "FakeRedis") -> None:
        self._redis = redis
        self._queue: list = []

    def incr(self, key: str):
        self._queue.append(("incr", key))
        return self

    def expire(self, key: str, seconds: int):
        self._queue.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for cmd in self._queue:
            if cmd[0] == "incr":
                results.append(await self._redis.incr(cmd[1]))
            elif cmd[0] == "expire":
                results.append(await self._redis.expire(cmd[1], cmd[2]))
        self._queue.clear()
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeRedis:
    """Minimal in-memory Redis mock sufficient for all AttendX test needs."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._expiry: dict = {}
        self._lists: dict = {}
        self._hashes: dict = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value, ex: int | None = None, **kwargs) -> bool:
        self._data[key] = value
        if ex is not None:
            self._expiry[key] = ex
        return True

    async def setex(self, key: str, seconds: int, value) -> bool:
        self._data[key] = value
        self._expiry[key] = seconds
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            for store in (self._data, self._lists, self._hashes, self._expiry):
                if key in store:
                    del store[key]
                    count += 1
                    break
        return count

    async def exists(self, *keys: str) -> int:
        return sum(
            1 for k in keys
            if k in self._data or k in self._lists or k in self._hashes
        )

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._data or key in self._lists:
            self._expiry[key] = seconds
            return True
        return False

    async def ttl(self, key: str) -> int:
        exists = key in self._data or key in self._lists or key in self._hashes
        if not exists:
            return -2
        return self._expiry.get(key, -1)

    async def incr(self, key: str) -> int:
        val = int(self._data.get(key, 0)) + 1
        self._data[key] = str(val)
        return val

    async def incrby(self, key: str, amount: int) -> int:
        val = int(self._data.get(key, 0)) + amount
        self._data[key] = str(val)
        return val

    async def lpush(self, key: str, *values) -> int:
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].insert(0, v)
        return len(self._lists[key])

    async def rpush(self, key: str, *values) -> int:
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].append(v)
        return len(self._lists[key])

    async def lrange(self, key: str, start: int, stop: int):
        lst = self._lists.get(key, [])
        if stop == -1:
            return lst[start:]
        return lst[start : stop + 1]

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        if key in self._lists:
            end = stop + 1 if stop != -1 else None
            self._lists[key] = self._lists[key][start:end]
        return True

    async def llen(self, key: str) -> int:
        return len(self._lists.get(key, []))

    async def lindex(self, key: str, index: int):
        lst = self._lists.get(key, [])
        try:
            return lst[index]
        except IndexError:
            return None

    async def lset(self, key: str, index: int, value) -> bool:
        if key in self._lists:
            self._lists[key][index] = value
            return True
        return False

    async def lrem(self, key: str, count: int, element) -> int:
        if key not in self._lists:
            return 0
        lst = self._lists[key]
        removed = 0
        new_lst = []
        for item in lst:
            if item == element and (count == 0 or removed < abs(count)):
                removed += 1
            else:
                new_lst.append(item)
        self._lists[key] = new_lst
        return removed

    async def hset(self, key: str, mapping: dict | None = None, **kwargs) -> int:
        if key not in self._hashes:
            self._hashes[key] = {}
        updates = {**(mapping or {}), **kwargs}
        self._hashes[key].update(updates)
        return len(updates)

    async def hget(self, key: str, field: str):
        return self._hashes.get(key, {}).get(field)

    async def hgetall(self, key: str) -> dict:
        return dict(self._hashes.get(key, {}))

    async def hdel(self, key: str, *fields: str) -> int:
        h = self._hashes.get(key, {})
        removed = sum(1 for f in fields if f in h)
        for f in fields:
            h.pop(f, None)
        return removed

    async def keys(self, pattern: str = "*"):
        all_keys = (
            list(self._data.keys())
            + list(self._lists.keys())
            + list(self._hashes.keys())
        )
        pat = pattern.replace("*", "*")
        return [k for k in all_keys if fnmatch.fnmatch(k, pat)]

    async def publish(self, channel: str, message: str) -> int:
        return 0

    async def close(self) -> None:
        pass

    def pipeline(self, transaction: bool = True):
        return FakePipeline(self)


# -- Fixtures ------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """
    Fresh in-memory SQLite session per test.

    StaticPool ensures all connections share the same in-memory database,
    which is required for :memory: + async SQLAlchemy to work correctly.
    """
    engine = create_async_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def fake_redis() -> FakeRedis:
    """Fresh FakeRedis instance per test."""
    return FakeRedis()


# -- User fixtures -------------------------------------------------------------


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Super-admin user."""
    user = User(
        id=uuid.uuid4(),
        username="testadmin",
        email="test@attendx.local",
        password_hash=hash_password("testpass123"),
        role="super_admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_teacher(db_session: AsyncSession) -> User:
    """Teacher user."""
    user = User(
        id=uuid.uuid4(),
        username="testteacher",
        email="teacher@attendx.local",
        password_hash=hash_password("testpass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(sample_user: User) -> dict[str, str]:
    """JWT Bearer headers for super_admin."""
    token = create_access_token(
        {"sub": str(sample_user.id), "role": sample_user.role, "jti": str(uuid.uuid4())}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_auth_headers(sample_teacher: User) -> dict[str, str]:
    """JWT Bearer headers for teacher."""
    token = create_access_token(
        {"sub": str(sample_teacher.id), "role": sample_teacher.role, "jti": str(uuid.uuid4())}
    )
    return {"Authorization": f"Bearer {token}"}


# -- Data fixtures -------------------------------------------------------------


@pytest.fixture
async def sample_students(db_session: AsyncSession) -> list[Student]:
    """10 students across two classes."""
    students = []
    for i in range(10):
        s = Student(
            id=uuid.uuid4(),
            name=f"Student {i + 1}",
            class_name="7-A" if i < 5 else "7-B",
            employee_no=f"STD{i:03d}",
            external_id=f"EXT{i:03d}",
            is_active=True,
        )
        db_session.add(s)
        students.append(s)
    await db_session.commit()
    for s in students:
        await db_session.refresh(s)
    return students


@pytest.fixture
async def sample_device(db_session: AsyncSession) -> Device:
    """A single active Hikvision device."""
    device = Device(
        name="Test Terminal",
        ip_address="192.168.1.100",
        port=80,
        username="admin",
        password_enc=encrypt_device_password("testpass"),
        is_entry=True,
        is_active=True,
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


@pytest.fixture
async def sample_attendance(
    db_session: AsyncSession,
    sample_students: list[Student],
    sample_device: Device,
) -> list[AttendanceLog]:
    """5 attendance entry records for the first 5 students."""
    logs = []
    for student in sample_students[:5]:
        log = AttendanceLog(
            id=uuid.uuid4(),
            student_id=student.id,
            device_id=sample_device.id,
            event_time=datetime.now(timezone.utc),
            event_type="entry",
            verify_mode="face",
            raw_event_id=f"RAW-{uuid.uuid4().hex[:8]}",
            notified=False,
        )
        db_session.add(log)
        logs.append(log)
    await db_session.commit()
    for log in logs:
        await db_session.refresh(log)
    return logs


@pytest.fixture
async def sample_webhook(db_session: AsyncSession, sample_user: User) -> Webhook:
    """A single active webhook."""
    wh = Webhook(
        id=uuid.uuid4(),
        url="https://webhook.example.com/attendx",
        secret="test-webhook-secret-key",
        events={"attendance.entry": True, "attendance.exit": True},
        is_active=True,
        description="Test webhook",
        created_by=sample_user.id,
    )
    db_session.add(wh)
    await db_session.commit()
    await db_session.refresh(wh)
    return wh


# -- HTTP client fixtures ------------------------------------------------------


@pytest.fixture
async def client(
    db_session: AsyncSession,
    sample_user: User,
    fake_redis: FakeRedis,
) -> AsyncIterator[AsyncClient]:
    """Async HTTP client authenticated as super_admin."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    async def _override_get_user():
        return sample_user

    def _override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_active_user] = _override_get_user
    app.dependency_overrides[get_redis] = _override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def teacher_client(
    db_session: AsyncSession,
    sample_teacher: User,
    fake_redis: FakeRedis,
) -> AsyncIterator[AsyncClient]:
    """Async HTTP client authenticated as teacher."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    async def _override_get_user():
        return sample_teacher

    def _override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_active_user] = _override_get_user
    app.dependency_overrides[get_redis] = _override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def anon_client() -> AsyncIterator[AsyncClient]:
    """Unauthenticated client (headers and dependency overrides not set)."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def db_anon_client(
    db_session: AsyncSession,
    fake_redis: FakeRedis,
) -> AsyncIterator[AsyncClient]:
    """Unauthenticated client with DB and Redis overrides (for testing real auth flow)."""
    from app.main import app

    async def _override_get_db():
        yield db_session

    def _override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = _override_get_redis
    # NOTE: get_current_active_user is NOT overridden — real JWT auth is used

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
