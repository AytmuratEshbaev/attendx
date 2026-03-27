Phase 1

You are setting up "AttendX" — a Face Recognition Attendance Platform that integrates with Hikvision terminals. This is Phase 1: Project Setup & Foundation.

## Project Overview
AttendX is a standalone platform for managing Hikvision face recognition terminals and monitoring attendance. It integrates with external systems (MBI-Chat, Kundalik, 1C) via REST API and Webhooks.

## Task: Initialize the complete monorepo with the following exact structure:

attendx/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Pydantic Settings with .env support
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # Main v1 router that includes all sub-routers
│   │   │       ├── auth.py            # Auth endpoints (login, refresh, logout, me)
│   │   │       ├── students.py        # Students CRUD + bulk import + face upload
│   │   │       ├── attendance.py      # Attendance list, today, stats, report
│   │   │       ├── devices.py         # Devices CRUD + sync + health
│   │   │       ├── webhooks.py        # Webhooks CRUD + logs + retry
│   │   │       └── reports.py         # Reports endpoints (PDF/Excel)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py            # JWT creation/verification, password hashing (bcrypt), API key validation
│   │   │   ├── exceptions.py          # Custom exceptions (NotFound, ValidationError, AuthError, DeviceError)
│   │   │   ├── permissions.py         # RBAC: SuperAdmin, Admin, Teacher, API roles
│   │   │   └── dependencies.py        # FastAPI dependencies (get_db, get_current_user, require_role)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # SQLAlchemy declarative base with common fields (id, created_at, updated_at)
│   │   │   ├── student.py             # Student model (UUID pk, external_id, employee_no, name, class_name, phone, parent_phone, face_registered, face_image_path, is_active)
│   │   │   ├── attendance.py          # AttendanceLog model (UUID pk, student_id FK, device_id FK, event_time, event_type entry/exit, verify_mode, raw_event_id UNIQUE, notified)
│   │   │   ├── device.py              # Device model (SERIAL pk, name, ip_address, port, username, password_enc, is_entry, is_active, last_online_at, model, serial_number)
│   │   │   ├── user.py                # User model (admin/teacher accounts - id, username, email, password_hash, role, is_active)
│   │   │   ├── webhook.py             # Webhook model (id, url, secret, events JSON, is_active, created_at)
│   │   │   ├── webhook_log.py         # WebhookLog model (id, webhook_id FK, event_type, payload, response_status, response_body, attempts, success)
│   │   │   ├── api_key.py             # APIKey model (id, key_hash, name, permissions, is_active, last_used_at)
│   │   │   ├── telegram_sub.py        # TelegramSub model (id, chat_id, phone, student_id FK, is_active)
│   │   │   └── audit_log.py           # AuditLog model (id, user_id, action, entity_type, entity_id, details JSON, ip_address, created_at)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── common.py              # SuccessResponse, ErrorResponse, PaginatedResponse, Meta schemas
│   │   │   ├── auth.py                # LoginRequest, TokenResponse, RefreshRequest
│   │   │   ├── student.py             # StudentCreate, StudentUpdate, StudentResponse, StudentImport
│   │   │   ├── attendance.py          # AttendanceResponse, AttendanceStats, AttendanceFilter
│   │   │   ├── device.py              # DeviceCreate, DeviceUpdate, DeviceResponse, DeviceHealth
│   │   │   └── webhook.py             # WebhookCreate, WebhookUpdate, WebhookResponse, WebhookLogResponse
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── student_service.py     # StudentService: CRUD + bulk import + face management (placeholder logic)
│   │   │   ├── attendance_service.py  # AttendanceService: query + stats + reports (placeholder logic)
│   │   │   ├── device_service.py      # DeviceService: CRUD + health check + sync trigger (placeholder logic)
│   │   │   ├── webhook_service.py     # WebhookService: CRUD + delivery + retry (placeholder logic)
│   │   │   └── notification_service.py # NotificationService: Telegram + webhook dispatch (placeholder logic)
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py                # BaseRepository: generic async CRUD (create, get, get_all, update, delete)
│   │       ├── student_repo.py        # StudentRepository
│   │       ├── attendance_repo.py     # AttendanceRepository
│   │       └── device_repo.py         # DeviceRepository
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── hikvision/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # TODO: HikvisionClient - async HTTP client with digest auth
│   │   │   ├── poller.py              # TODO: EventPoller - polling scheduler (5 sec interval)
│   │   │   └── sync.py                # TODO: UserSync - face registration & user sync
│   │   └── notifications/
│   │       ├── __init__.py
│   │       └── processor.py           # TODO: NotificationProcessor - Redis queue consumer
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py                    # TODO: Bot entry point
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py               # TODO: /start handler + phone verification
│   │   │   ├── attendance.py          # TODO: /davomat handler
│   │   │   └── settings.py            # TODO: /sozlamalar handler
│   │   └── keyboards.py               # TODO: Telegram keyboards
│   ├── alembic/
│   │   └── env.py                     # Alembic async config for SQLAlchemy 2.0
│   ├── alembic.ini
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                # Pytest fixtures: async db session, test client, sample data
│   │   ├── test_health.py             # Health check endpoint test
│   │   └── test_auth.py               # Auth endpoint placeholder tests
│   ├── pyproject.toml                 # Poetry config with all dependencies
│   └── Dockerfile                     # Multi-stage: builder + runtime
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css                  # Tailwind imports
│   │   ├── components/
│   │   │   └── ui/                    # shadcn/ui components (button, input, card, table, dialog, toast)
│   │   ├── pages/
│   │   │   ├── Login.tsx              # Login page placeholder
│   │   │   ├── Dashboard.tsx          # Dashboard placeholder
│   │   │   ├── Students.tsx           # Students page placeholder
│   │   │   ├── Attendance.tsx         # Attendance page placeholder
│   │   │   ├── Devices.tsx            # Devices page placeholder
│   │   │   ├── Webhooks.tsx           # Webhooks page placeholder
│   │   │   ├── Reports.tsx            # Reports page placeholder
│   │   │   └── Settings.tsx           # Settings page placeholder
│   │   ├── hooks/
│   │   │   └── useAuth.ts             # Auth hook placeholder
│   │   ├── services/
│   │   │   └── api.ts                 # Axios instance with JWT interceptor
│   │   ├── store/
│   │   │   └── authStore.ts           # Zustand auth store
│   │   └── types/
│   │       └── index.ts               # TypeScript interfaces matching backend schemas
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── index.html
│   └── Dockerfile
├── docker/
│   ├── docker-compose.yml             # Dev: backend(8000), frontend(3000), postgres(5432), redis(6379), nginx(80)
│   ├── docker-compose.prod.yml        # Production optimized
│   ├── nginx.conf                     # Reverse proxy: /api -> backend, / -> frontend
│   └── .dockerignore
├── docs/
│   ├── installation.md
│   ├── admin-guide.md
│   ├── api-reference.md
│   └── troubleshooting.md
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml            # black, ruff, mypy hooks
├── README.md
├── LICENSE                            # MIT
└── CONTRIBUTING.md                    # Branch strategy: main, develop, feature/*

## Key Technical Requirements:

### Backend (pyproject.toml):
- Python 3.11+
- Dependencies: fastapi>=0.110, uvicorn[standard], sqlalchemy[asyncio]>=2.0, asyncpg, alembic, pydantic-settings, redis[hiredis], httpx, python-jose[cryptography], passlib[bcrypt], cryptography, python-telegram-bot>=20, structlog, tenacity, python-multipart, openpyxl
- Dev: pytest, pytest-asyncio, httpx (test client), black, ruff, mypy, pre-commit

### Frontend (package.json with pnpm):
- React 18 + TypeScript strict
- Vite as bundler
- Dependencies: tailwindcss, @shadcn/ui, react-router-dom@6, @tanstack/react-query, zustand, axios, recharts, react-hook-form, zod, sonner

### Docker Compose (dev):
- backend: Python FastAPI on port 8000, volume mount ./backend:/app
- frontend: Vite dev server on port 3000, volume mount ./frontend:/app
- db: postgres:15-alpine, POSTGRES_DB=attendx, POSTGRES_USER=attendx, POSTGRES_PASSWORD=attendx_dev, port 5432, persistent volume
- redis: redis:7-alpine, port 6379, persistent volume
- nginx: port 80, proxy /api to backend:8000, proxy / to frontend:3000
- Network: attendx-network

### .env.example:
DATABASE_URL=postgresql+asyncpg://attendx:attendx_dev@db:5432/attendx
DATABASE_URL_SYNC=postgresql://attendx:attendx_dev@db:5432/attendx
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-me-to-random-64-char-string
JWT_SECRET=change-me-to-random-32-char-string
JWT_ACCESS_EXPIRY_MINUTES=60
JWT_REFRESH_EXPIRY_DAYS=7
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
FERNET_KEY=generate-with-cryptography-fernet
API_KEY_HEADER=X-API-Key
DEFAULT_API_KEY=change-me-initial-api-key
SENTRY_DSN=
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80

### main.py must include:
1. FastAPI app with title="AttendX API", description="Face Recognition Attendance Platform", version="1.0.0"
2. CORS middleware with configurable origins from settings
3. Structured logging with structlog (JSON format)
4. Custom exception handlers returning: {"success": false, "error": {"code": "...", "message": "..."}, "meta": {"timestamp": "..."}}
5. Health check: GET /health -> {"status": "ok", "version": "1.0.0", "timestamp": "..."}
6. Include v1 router at prefix /api/v1
7. Lifespan event: startup (db pool, redis connection), shutdown (cleanup)

### SQLAlchemy Models:
- Use SQLAlchemy 2.0 async style (Mapped, mapped_column)
- All UUID primary keys use uuid4 default
- All models have created_at (server_default=func.now()) and updated_at (onupdate=func.now())
- Proper indexes: attendance_logs(student_id, event_time), attendance_logs(raw_event_id) UNIQUE, students(external_id) UNIQUE, students(employee_no) UNIQUE, students(class_name)

### Repository Pattern:
- BaseRepository with generic type T
- Methods: create(data), get(id), get_all(skip, limit, filters), update(id, data), delete(id, soft=True)
- All async using AsyncSession

### Important Notes:
- Worker (hikvision/) and Bot (bot/) directories should have TODO placeholder files only — they will be implemented in Phase 3 and Phase 7
- Services should have real method signatures but can have placeholder/minimal implementations
- API route files should have route decorators with correct paths, methods, and response models, but can have minimal implementations
- All files must have proper type hints
- Use absolute imports: from app.models.student import Student

Initialize git, create initial commit "feat: project setup - Phase 1", and ensure everything is ready for Phase 2 (Backend Core implementation).
```

---

Phase 2

We are continuing AttendX development. Phase 1 (project setup) is complete. Now implement Phase 2: Backend Core. The project structure already exists — you need to fill in the actual implementations.

Read the existing codebase first to understand the current structure, then implement everything below.

## TASK: Phase 2 — Backend Core (Full Implementation)

---

### PART 1: Configuration & App Setup

**app/config.py — Pydantic Settings:**
- Class Settings(BaseSettings) with model_config = SettingsConfigDict(env_file=".env")
- Fields: DATABASE_URL, DATABASE_URL_SYNC, REDIS_URL, SECRET_KEY, JWT_SECRET, JWT_ACCESS_EXPIRY_MINUTES(60), JWT_REFRESH_EXPIRY_DAYS(7), TELEGRAM_BOT_TOKEN, FERNET_KEY, API_KEY_HEADER("X-API-Key"), DEFAULT_API_KEY, SENTRY_DSN(optional), LOG_LEVEL("INFO"), ALLOWED_ORIGINS(list, comma-separated)
- Singleton pattern: get_settings() with lru_cache

**app/main.py — Full setup:**
- Lifespan context manager: on startup create async engine, sessionmaker, redis connection pool; on shutdown dispose engine, close redis
- CORS middleware with settings.ALLOWED_ORIGINS
- Structured logging with structlog: JSON processor, timestamp, log level
- Custom exception handlers:
  - RequestValidationError -> 422, {"success": false, "error": {"code": "VALIDATION_ERROR", "message": field errors}, "meta": {"timestamp": iso}}
  - HTTPException -> appropriate status, same format
  - Generic Exception -> 500, {"success": false, "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}, "meta": {...}}
  - AttendXException -> custom status, same format
- Include v1 router at /api/v1
- Health check: GET /health -> {"status": "ok", "version": "1.0.0", "database": "connected/error", "redis": "connected/error", "timestamp": iso}

---

### PART 2: Database Layer

**app/models/base.py:**
- AsyncEngine and async_sessionmaker setup
- Base class using DeclarativeBase
- Mixin TimestampMixin: created_at (TIMESTAMPTZ, server_default=func.now()), updated_at (TIMESTAMPTZ, onupdate=func.now())
- async get_db() generator yielding AsyncSession
- init_db() to create engine from settings

**app/models/student.py — Student model:**
- __tablename__ = "students"
- id: UUID PK (default uuid4)
- external_id: String(100), unique, nullable, indexed
- employee_no: String(50), unique, indexed (Hikvision employee number)
- name: String(200), not null
- class_name: String(50), nullable, indexed
- phone: String(20), nullable
- parent_phone: String(20), nullable
- face_registered: Boolean, default False
- face_image_path: String(500), nullable
- is_active: Boolean, default True
- Relationships: attendance_logs, telegram_subs

**app/models/attendance.py — AttendanceLog model:**
- __tablename__ = "attendance_logs"
- Composite index: (student_id, event_time)
- Index: (event_time)
- id: UUID PK
- student_id: UUID FK -> students.id
- device_id: Integer FK -> devices.id
- event_time: TIMESTAMPTZ, not null
- event_type: String(10) — "entry" or "exit"
- verify_mode: String(20), default "face"
- raw_event_id: String(100), UNIQUE (deduplication)
- notified: Boolean, default False
- Relationships: student, device

**app/models/device.py — Device model:**
- __tablename__ = "devices"
- id: SERIAL PK (Integer, autoincrement)
- name: String(100)
- ip_address: String(45)
- port: Integer, default 80
- username: String(50)
- password_enc: Text (Fernet encrypted)
- is_entry: Boolean, default True
- is_active: Boolean, default True
- last_online_at: TIMESTAMPTZ, nullable
- model: String(100), nullable
- serial_number: String(100), nullable
- Relationship: attendance_logs

**Implement ALL other models:**
- user.py: User (id UUID, username unique, email, password_hash, role enum, is_active, last_login_at)
- webhook.py: Webhook (id UUID, url, secret, events JSONB array, is_active, created_by FK)
- webhook_log.py: WebhookLog (id UUID, webhook_id FK, event_type, payload JSONB, response_status int, response_body text, attempts int, success bool)
- api_key.py: APIKey (id UUID, key_hash, name, permissions JSONB, is_active, last_used_at, created_by FK)
- telegram_sub.py: TelegramSub (id UUID, chat_id bigint, phone, student_id FK, is_active)
- audit_log.py: AuditLog (id UUID, user_id FK nullable, action, entity_type, entity_id, details JSONB, ip_address, created_at)

**app/models/__init__.py:** Import all models, __all__ list

**Alembic setup:**
- Configure alembic/env.py for async SQLAlchemy 2.0 (run_async_migrations pattern)
- target_metadata = Base.metadata
- Generate initial migration creating ALL tables with indexes and constraints

---

### PART 3: Authentication System

**app/core/security.py:**
- create_access_token(data: dict) -> str: JWT with HS256, expiry from settings
- create_refresh_token(data: dict) -> str: longer expiry (7 days)
- decode_token(token: str) -> dict: decode and validate
- pwd_context = CryptContext(schemes=["bcrypt"])
- hash_password(password) -> str
- verify_password(plain, hashed) -> bool
- encrypt_device_password(password) -> str: Fernet encryption
- decrypt_device_password(encrypted) -> str: Fernet decryption
- hash_api_key(key) -> str: SHA256
- verify_api_key(key, hashed) -> bool

**app/core/permissions.py:**
- Role enum: SUPER_ADMIN, ADMIN, TEACHER, API
- ROLE_HIERARCHY dict with numeric levels
- has_permission(user_role, required_role) -> bool

**app/core/dependencies.py:**
- get_db(): AsyncSession generator
- get_current_user(token): decode JWT, query user, check Redis blacklist
- get_current_active_user(user): check is_active
- require_role(min_role): dependency factory checking role hierarchy
- get_api_key_user(api_key header): validate X-API-Key
- get_redis(): return Redis connection

**app/core/exceptions.py:**
- AttendXException(code, message, status_code)
- NotFoundError(entity, id) -> 404
- AuthenticationError(message) -> 401
- AuthorizationError(message) -> 403
- ValidationError(message) -> 422
- DeviceError(message) -> 502
- DuplicateError(entity, field) -> 409

---

### PART 4: Pydantic Schemas (all in app/schemas/)

**common.py:**
- Meta(timestamp, request_id)
- SuccessResponse[T](success=True, data: T, meta)
- ErrorDetail(code, message, details)
- ErrorResponse(success=False, error: ErrorDetail, meta)
- PaginationParams(cursor, limit 1-100)
- PaginatedResponse[T](success=True, data: list[T], meta, pagination dict)

**auth.py:**
- LoginRequest(username 3-50, password 6+)
- TokenResponse(access_token, refresh_token, token_type, expires_in)
- RefreshRequest(refresh_token)
- UserResponse(id, username, email, role, is_active) from_attributes=True

**student.py:**
- StudentBase(name, class_name, phone with regex, parent_phone, external_id)
- StudentCreate(StudentBase + employee_no required)
- StudentUpdate(all optional)
- StudentResponse(full fields, from_attributes=True)
- StudentImportRow(name, employee_no, class_name, phone, parent_phone, external_id)
- StudentImportResult(total, created, updated, errors list)

**attendance.py:**
- AttendanceResponse(id, student_id, student_name, device_name, event_time, event_type, verify_mode)
- AttendanceFilter(date_from, date_to, class_name, student_id)
- AttendanceStats(total_students, present, absent, percentage, period_data list)
- DailyAttendance(date, present, absent, percentage)

**device.py:**
- DeviceCreate(name, ip_address, port, username, password, is_entry)
- DeviceUpdate(all optional)
- DeviceResponse(all fields except password_enc, from_attributes=True)
- DeviceHealth(device_id, is_online, last_seen, model, serial_number)

**webhook.py:**
- WebhookCreate(url HttpUrl, secret, events list of event types, is_active)
- WebhookUpdate(all optional)
- WebhookResponse(all fields, from_attributes=True)
- WebhookLogResponse(id, webhook_id, event_type, response_status, attempts, success, created_at)

---

### PART 5: Repository Layer

**app/repositories/base.py — BaseRepository[T]:**
- __init__(session: AsyncSession, model: type[T])
- create(data: dict) -> T
- get(id) -> T | None
- get_or_raise(id) -> T (raises NotFoundError)
- get_all(skip, limit, filters, order_by) -> tuple[list[T], int]
- update(id, data: dict) -> T
- soft_delete(id) -> T

**app/repositories/student_repo.py — StudentRepository(BaseRepository[Student]):**
- get_by_employee_no(employee_no) -> Student | None
- get_by_external_id(external_id) -> Student | None
- get_by_class(class_name, skip, limit) -> tuple[list, int]
- search(query: str, skip, limit) -> tuple[list, int]: search by name ILIKE
- bulk_create(students_data: list[dict]) -> list[Student]

**app/repositories/attendance_repo.py — AttendanceRepository:**
- get_by_date_range(start, end, filters) -> list[AttendanceLog]
- get_today(class_name?) -> list[AttendanceLog]
- get_stats(period, class_name?, date_from?, date_to?) -> dict
- check_duplicate(raw_event_id) -> bool

**app/repositories/device_repo.py — DeviceRepository:**
- get_active_devices() -> list[Device]
- get_by_ip(ip_address) -> Device | None
- update_last_online(id) -> Device

---

### PART 6: Service Layer

**app/services/student_service.py — StudentService:**
- create_student(data: StudentCreate) -> Student: check duplicates, create
- get_student(id) -> Student
- list_students(skip, limit, class_name?, search?) -> tuple[list, int]
- update_student(id, data: StudentUpdate) -> Student
- delete_student(id) -> Student: soft delete
- import_from_excel(file: UploadFile) -> StudentImportResult: read with openpyxl, validate, upsert
- register_face(id, image: UploadFile) -> Student: validate JPEG max 200KB, save to media/faces/

**app/services/attendance_service.py — AttendanceService:**
- get_attendance(date_from, date_to, class_name, student_id, skip, limit) -> tuple[list, int]
- get_today(class_name?) -> list[dict]: grouped by student
- get_stats(period, class_name?, date_from?, date_to?) -> dict: counts + percentages
- record_event(student_id, device_id, event_time, event_type, verify_mode, raw_event_id) -> AttendanceLog | None
- export_report(format, date_from, date_to, class_name?) -> bytes: Excel with openpyxl

**app/services/device_service.py — DeviceService:**
- create_device(data: DeviceCreate) -> Device: encrypt password
- get_device(id) -> Device
- list_devices() -> list[Device]
- update_device(id, data: DeviceUpdate) -> Device
- delete_device(id) -> soft delete
- check_health(id) -> DeviceHealth: based on last_online_at for now

---

### PART 7: API Endpoints (full implementation)

**app/api/v1/auth.py:**
- POST /login -> TokenResponse
- POST /refresh -> TokenResponse
- POST /logout -> add token to Redis blacklist
- GET /me -> UserResponse

**app/api/v1/students.py (require Admin role):**
- GET / -> PaginatedResponse[StudentResponse] (query: skip, limit, class_name, search)
- POST / -> SuccessResponse[StudentResponse] (201)
- GET /{id} -> SuccessResponse[StudentResponse]
- PUT /{id} -> SuccessResponse[StudentResponse]
- DELETE /{id} -> SuccessResponse with message
- POST /{id}/face -> SuccessResponse[StudentResponse] (UploadFile)
- POST /import -> SuccessResponse[StudentImportResult] (UploadFile)
- GET /export -> StreamingResponse Excel file

**app/api/v1/attendance.py (require Teacher role):**
- GET / -> PaginatedResponse[AttendanceResponse] (query: date_from, date_to, class_name, student_id)
- GET /today -> SuccessResponse with today's data
- GET /stats -> SuccessResponse[AttendanceStats] (query: period, class_name, date_from, date_to)
- GET /report -> StreamingResponse Excel/PDF

**app/api/v1/devices.py (require Admin role):**
- GET / -> SuccessResponse[list[DeviceResponse]]
- POST / -> SuccessResponse[DeviceResponse] (201)
- PUT /{id} -> SuccessResponse[DeviceResponse]
- DELETE /{id} -> SuccessResponse
- POST /{id}/sync -> SuccessResponse (placeholder: "Sync triggered")
- GET /{id}/health -> SuccessResponse[DeviceHealth]

**app/api/v1/webhooks.py (require Admin role):**
- GET / -> list webhooks
- POST / -> create webhook
- PUT /{id} -> update webhook
- DELETE /{id} -> delete webhook
- GET /{id}/logs -> webhook delivery logs
- POST /{id}/test -> send test ping

**app/api/v1/reports.py (require Teacher role):**
- GET /daily -> daily report
- GET /weekly -> weekly report
- GET /monthly -> monthly report

**app/api/v1/router.py:** Include all sub-routers

---

### PART 8: Seed Data & Migration

**backend/scripts/seed.py:**
Create async seed script that adds:
1. SuperAdmin: username="admin", password="admin123", role=super_admin
2. Teacher: username="teacher", password="teacher123", role=teacher
3. 5 sample students in classes "5-A" and "6-B" with employee_no "EMP001"-"EMP005"
4. 1 sample device: name="Main Entrance", ip=192.168.1.100, port=80, username=admin, password encrypted
5. 1 default API key

Run: alembic revision --autogenerate -m "initial_tables"

---

### PART 9: Tests

**tests/conftest.py:**
- Async test setup with separate test database (sqlite+aiosqlite or test postgres)
- AsyncClient fixture with httpx
- Override get_db dependency
- Fixtures: test_user, test_student, test_device, auth_headers

**Write tests for:**
- test_health.py: GET /health -> 200
- test_auth.py: login success/fail, /me with/without token, refresh
- test_students.py: CRUD, duplicate check, class filter, auth required, role check

After ALL implementation is complete:
1. Generate alembic migration
2. Run all tests and fix any failures
3. Verify swagger docs at /docs work correctly
4. Commit: "feat: backend core implementation - Phase 2"
```

Phase 3

This is Phase 3 of "AttendX" — Face Recognition Attendance Platform. Phase 1 (project setup) and Phase 2 (backend core) are complete. Now implement the Hikvision Worker fully.

Read the existing codebase first to understand models, services, config, and database setup before making changes.

## TASK: Implement Hikvision Worker (Phase 3)

The Hikvision Worker is a separate background process that communicates with Hikvision face recognition terminals via ISAPI protocol. It polls events, syncs users/faces, and monitors terminal health.

### 1. HikvisionClient (backend/worker/hikvision/client.py):

This is the core HTTP client for communicating with Hikvision terminals via ISAPI.

```python
class HikvisionClient:
    """Async HTTP client for Hikvision ISAPI protocol."""

    def __init__(self, ip: str, port: int, username: str, password: str):
        self.base_url = f"http://{ip}:{port}"
        self.auth = httpx.DigestAuth(username, password)  # Hikvision uses HTTP Digest Auth
        self.client: httpx.AsyncClient | None = None
        self.timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)

    async def connect(self) -> None:
        """Create httpx.AsyncClient with digest auth, timeout, and retry."""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self.auth,
            timeout=self.timeout,
            verify=False,  # Hikvision terminals use self-signed certs
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()

    async def __aenter__(self): ...
    async def __aexit__(self, *args): ...
```

**Implement these ISAPI methods:**

**get_device_info() -> dict:**
- GET /ISAPI/System/deviceInfo
- Parse XML response (use xml.etree.ElementTree)
- Return: {device_name, model, serial_number, firmware_version, mac_address}
- Raise DeviceException on connection error

**add_user(employee_no: str, name: str) -> bool:**
- POST /ISAPI/AccessControl/UserInfo/Record
- XML body:
```xml
<UserInfo>
    <employeeNo>{employee_no}</employeeNo>
    <name>{name}</name>
    <userType>normal</userType>
    <Valid>
        <enable>true</enable>
        <beginTime>2020-01-01T00:00:00</beginTime>
        <endTime>2037-12-31T23:59:59</endTime>
    </Valid>
    <doorRight>1</doorRight>
    <RightPlan>
        <doorNo>1</doorNo>
        <planTemplateNo>1</planTemplateNo>
    </RightPlan>
</UserInfo>
```
- Return True on success (status 200, responseStatusStrg="OK")
- Handle: duplicate user (already exists → return True), connection error

**update_user(employee_no: str, name: str) -> bool:**
- PUT /ISAPI/AccessControl/UserInfo/Modify
- Same XML structure as add_user
- Return True on success

**delete_user(employee_no: str) -> bool:**
- PUT /ISAPI/AccessControl/UserInfo/Delete
- XML body:
```xml
<UserInfoDelCond>
    <EmployeeNoList>
        <employeeNo>{employee_no}</employeeNo>
    </EmployeeNoList>
</UserInfoDelCond>
```
- Return True on success

**register_face(employee_no: str, image_data: bytes) -> bool:**
- POST /ISAPI/Intelligent/FDLib/FaceDataRecord
- Multipart upload:
  - Part 1: JSON metadata {"faceLibType": "blackFD", "FDID": "1", "FPID": employee_no}
  - Part 2: JPEG image data (content-type: image/jpeg)
- Validate image before upload:
  - Must be JPEG format
  - Max 200KB size
  - If larger, resize/compress using Pillow
- Return True on success
- Handle: face already exists → delete old face first, then re-register

**delete_face(employee_no: str) -> bool:**
- PUT /ISAPI/Intelligent/FDLib/FDSearch/Delete
- Delete face data for the given employee
- XML body with FPID filter

**get_events(start_time: datetime, end_time: datetime, position: int = 0) -> dict:**
- POST /ISAPI/AccessControl/AcsEvent
- XML body:
```xml
<AcsEventCond>
    <searchID>attendx-{uuid4}</searchID>
    <searchResultPosition>{position}</searchResultPosition>
    <maxResults>50</maxResults>
    <major>0</major>
    <minor>0</minor>
    <startTime>{start_time ISO format}</startTime>
    <endTime>{end_time ISO format}</endTime>
</AcsEventCond>
```
- Parse XML response, extract events list:
  Each event: {event_id, employee_no, name, event_time, event_type(entry/exit), verify_mode, door_no}
- Handle pagination: if totalMatches > position + numOfMatches, there are more pages
- Return: {events: list, total: int, has_more: bool, next_position: int}

**search_users(position: int = 0) -> dict:**
- POST /ISAPI/AccessControl/UserInfo/Search
- XML body:
```xml
<UserInfoSearchCond>
    <searchID>attendx-{uuid4}</searchID>
    <searchResultPosition>{position}</searchResultPosition>
    <maxResults>50</maxResults>
</UserInfoSearchCond>
```
- Return: {users: list[{employee_no, name}], total: int, has_more: bool}

**check_online() -> bool:**
- GET /ISAPI/System/deviceInfo with short timeout (5 sec)
- Return True if responds, False if connection error/timeout

**Add retry decorator to all methods using tenacity:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
```

**Custom exceptions (backend/worker/hikvision/exceptions.py):**
- HikvisionError(Exception): base
- DeviceOfflineError(HikvisionError): terminal unreachable
- AuthenticationError(HikvisionError): wrong credentials (401)
- ISAPIError(HikvisionError): ISAPI returned error response
- FaceRegistrationError(HikvisionError): face upload failed
- UserSyncError(HikvisionError): user add/delete failed

**XML helpers (backend/worker/hikvision/xml_helpers.py):**
- build_xml(tag, data: dict) -> str: Build XML string from dict
- parse_xml_response(content: bytes) -> dict: Parse ISAPI XML response
- extract_events_from_xml(content: bytes) -> list[dict]: Parse event list
- extract_users_from_xml(content: bytes) -> list[dict]: Parse user list
- get_response_status(content: bytes) -> tuple[bool, str]: Check if ISAPI response is OK


### 2. EventPoller (backend/worker/hikvision/poller.py):

Background process that polls all active terminals for new events.

```python
class EventPoller:
    def __init__(self, db_session_factory, redis_client):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.clients: dict[int, HikvisionClient] = {}  # device_id -> client
        self.running = False
        self.poll_interval = settings.HIKVISION_POLL_INTERVAL  # default 5 sec

    async def start(self) -> None:
        """Start the polling loop."""
        self.running = True
        await self._initialize_clients()
        while self.running:
            try:
                await self._poll_all_devices()
            except Exception as e:
                logger.error("Polling cycle error", error=str(e))
            await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Graceful shutdown."""
        self.running = False
        for client in self.clients.values():
            await client.close()

    async def _initialize_clients(self) -> None:
        """Load active devices from DB, create HikvisionClient for each."""
        async with self.db_session_factory() as session:
            repo = DeviceRepository(Device, session)
            devices = await repo.get_active_devices()
            for device in devices:
                password = decrypt_device_password(device.password_enc)
                client = HikvisionClient(device.ip_address, device.port, device.username, password)
                await client.connect()
                self.clients[device.id] = client

    async def _poll_all_devices(self) -> None:
        """Poll all devices concurrently using asyncio.gather."""
        tasks = [
            self._poll_device(device_id, client)
            for device_id, client in self.clients.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _poll_device(self, device_id: int, client: HikvisionClient) -> None:
        """Poll single device for new events since last poll."""
        # Get last poll timestamp from Redis: f"device:{device_id}:last_poll"
        # If no last_poll, use now - 10 seconds
        # Call client.get_events(start_time, end_time)
        # Handle pagination (while has_more)
        # For each event: process_event()
        # Update last_poll in Redis

    async def _process_event(self, device_id: int, event: dict) -> None:
        """Process a single event from terminal."""
        # 1. Check duplicate: raw_event_id in DB (attendance_repo.check_duplicate)
        # 2. Find student by employee_no
        # 3. Determine event_type: use device.is_entry to decide entry/exit
        # 4. Insert attendance_log via attendance_service.record_event()
        # 5. Publish to Redis notification queue: f"notifications:attendance"
        #    Payload: {student_id, student_name, class_name, event_type, event_time, device_name}
        # 6. Log the event

    async def refresh_clients(self) -> None:
        """Reload device list (when devices added/removed via admin panel)."""
        await self.stop()
        self.clients.clear()
        self.running = True
        await self._initialize_clients()
```

**Last poll tracking with Redis:**
- Key: `device:{device_id}:last_poll`
- Value: ISO timestamp
- On each successful poll, update this key
- On first poll (no key), start from current_time - 10 seconds

**Deduplication:**
- Use raw_event_id (from terminal) + dedup window (5 min)
- Also cache in Redis: `event:dedup:{raw_event_id}` with 5 min TTL
- Check Redis first (fast), then DB (reliable)


### 3. UserSync (backend/worker/hikvision/sync.py):

Handles syncing students to/from Hikvision terminals.

```python
class UserSync:
    def __init__(self, db_session_factory, clients: dict[int, HikvisionClient]):
        self.db_session_factory = db_session_factory
        self.clients = clients

    async def sync_student_to_all_devices(self, student_id: UUID) -> dict:
        """Add/update a student on all active terminals."""
        # 1. Get student from DB
        # 2. For each active device client:
        #    - add_user(employee_no, name)
        #    - if face_registered and face_image_path: register_face(employee_no, image_bytes)
        # 3. Return: {success: list[device_id], failed: list[{device_id, error}]}

    async def remove_student_from_all_devices(self, employee_no: str) -> dict:
        """Remove a student from all terminals (on student delete)."""
        # For each device: delete_face(), then delete_user()

    async def sync_face_to_all_devices(self, student_id: UUID, image_path: str) -> dict:
        """Register face image on all terminals."""
        # 1. Read image from face_image_path
        # 2. Validate JPEG, check size <= 200KB, compress if needed
        # 3. For each device: register_face(employee_no, image_bytes)

    async def full_sync(self, device_id: int) -> dict:
        """Full sync: compare DB students with terminal users, reconcile differences."""
        # 1. Get all active students from DB
        # 2. Get all users from terminal (search_users, paginate)
        # 3. Compare:
        #    - In DB but not terminal → add_user + register_face
        #    - In terminal but not DB → delete_user (optional, configurable)
        #    - In both → check if face needs update
        # 4. Return: {added: int, removed: int, updated: int, errors: list}

    async def bulk_register_faces(self, student_ids: list[UUID]) -> dict:
        """Register faces for multiple students on all devices."""
        # Process in batches of 10 to avoid overwhelming terminals
        # Use asyncio.Semaphore(5) to limit concurrent terminal connections

    @staticmethod
    def validate_face_image(image_data: bytes) -> bytes:
        """Validate and prepare face image for Hikvision terminal."""
        # Check JPEG format (starts with FF D8)
        # If not JPEG, convert using Pillow
        # If > 200KB, resize maintaining aspect ratio until under 200KB
        # Recommended: 640x480 or smaller
        # Return processed bytes
```

**Add Pillow to dependencies (pyproject.toml):**
- Pillow >= 10.0


### 4. HealthChecker (backend/worker/hikvision/health.py):

Monitors terminal online/offline status.

```python
class HealthChecker:
    def __init__(self, db_session_factory, clients: dict[int, HikvisionClient], redis_client):
        self.db_session_factory = db_session_factory
        self.clients = clients
        self.redis = redis_client
        self.check_interval = 30  # seconds
        self.running = False

    async def start(self) -> None:
        """Start health check loop."""
        self.running = True
        while self.running:
            await self._check_all_devices()
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        self.running = False

    async def _check_all_devices(self) -> None:
        """Check all devices concurrently."""
        tasks = [
            self._check_device(device_id, client)
            for device_id, client in self.clients.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_device(self, device_id: int, client: HikvisionClient) -> None:
        """Check single device health."""
        start = time.monotonic()
        is_online = await client.check_online()
        response_time = (time.monotonic() - start) * 1000  # ms

        # Get previous status from Redis
        prev_status_key = f"device:{device_id}:online"
        prev_online = await self.redis.get(prev_status_key)

        # Update Redis status
        await self.redis.set(prev_status_key, "1" if is_online else "0")
        await self.redis.set(f"device:{device_id}:response_time", str(int(response_time)))

        # Update DB: device.last_online_at
        if is_online:
            async with self.db_session_factory() as session:
                repo = DeviceRepository(Device, session)
                await repo.update_online_status(device_id, True)
                await session.commit()

        # Detect status change → trigger notification
        if prev_online is not None:
            was_online = prev_online == b"1"
            if was_online and not is_online:
                # Device went OFFLINE → publish alert
                await self.redis.publish("notifications:device", json.dumps({
                    "device_id": device_id,
                    "event": "device.offline",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                logger.warning("Device went offline", device_id=device_id)
            elif not was_online and is_online:
                # Device came ONLINE → publish alert
                await self.redis.publish("notifications:device", json.dumps({
                    "device_id": device_id,
                    "event": "device.online",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                logger.info("Device came online", device_id=device_id)
```


### 5. NotificationProcessor (backend/worker/notifications/processor.py):

Consumes events from Redis queue and dispatches to Telegram + Webhooks.

```python
class NotificationProcessor:
    def __init__(self, db_session_factory, redis_client):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.running = False

    async def start(self) -> None:
        """Subscribe to Redis channels and process notifications."""
        self.running = True
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("notifications:attendance", "notifications:device")

        while self.running:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                channel = message["channel"]
                data = json.loads(message["data"])

                if channel == b"notifications:attendance":
                    await self._handle_attendance_notification(data)
                elif channel == b"notifications:device":
                    await self._handle_device_notification(data)

    async def stop(self) -> None:
        self.running = False

    async def _handle_attendance_notification(self, data: dict) -> None:
        """Send attendance notification to Telegram subscribers and webhooks."""
        student_id = data["student_id"]
        event_type = data["event_type"]  # entry or exit

        # 1. Find Telegram subscribers for this student
        async with self.db_session_factory() as session:
            # Query telegram_subs where student_id matches and is_active
            # For each subscriber: send Telegram message

            # 2. Find active webhooks subscribed to attendance.entry/exit
            # For each webhook: queue HTTP POST delivery

        # 3. Mark attendance_log as notified=True

    async def _send_telegram_message(self, chat_id: int, message: str) -> bool:
        """Send message via Telegram Bot API."""
        # Use httpx to call Telegram API directly (not python-telegram-bot here)
        # POST https://api.telegram.org/bot{token}/sendMessage
        # Handle rate limiting (30 msg/sec Telegram limit)
        # Return True on success

    async def _deliver_webhook(self, webhook, event_type: str, payload: dict) -> bool:
        """Deliver webhook with HMAC signature."""
        # 1. Generate HMAC-SHA256 signature: hmac.new(webhook.secret, json_payload, sha256)
        # 2. POST to webhook.url with headers:
        #    - Content-Type: application/json
        #    - X-AttendX-Signature: sha256={signature}
        #    - X-AttendX-Event: {event_type}
        #    - X-AttendX-Delivery: {uuid4}
        # 3. Log to webhook_logs table
        # 4. If failed, retry (3x exponential backoff: 10s, 60s, 300s)

    @staticmethod
    def format_attendance_message(data: dict) -> str:
        """Format Telegram notification message."""
        if data["event_type"] == "entry":
            emoji = "✅"
            action = "maktabga keldi"
        else:
            emoji = "🏠"
            action = "maktabdan ketdi"

        return (
            f"{emoji} {data['student_name']}\n"
            f"📚 {data['class_name']}\n"
            f"🕐 {data['event_time']}\n"
            f"📍 {data.get('device_name', '')}\n"
            f"_{action}_"
        )
```


### 6. Worker Main Entry Point (backend/worker/main.py):

```python
"""
AttendX Hikvision Worker — Background process for terminal communication.

Run: python -m worker.main
"""
import asyncio
import signal
from worker.hikvision.poller import EventPoller
from worker.hikvision.health import HealthChecker
from worker.notifications.processor import NotificationProcessor

class WorkerManager:
    def __init__(self):
        self.poller: EventPoller | None = None
        self.health_checker: HealthChecker | None = None
        self.notification_processor: NotificationProcessor | None = None

    async def start(self) -> None:
        """Initialize and start all worker components."""
        # 1. Initialize database session factory (async)
        # 2. Initialize Redis client
        # 3. Create EventPoller, HealthChecker, NotificationProcessor
        # 4. Run all three concurrently:
        await asyncio.gather(
            self.poller.start(),
            self.health_checker.start(),
            self.notification_processor.start(),
        )

    async def shutdown(self) -> None:
        """Graceful shutdown of all components."""
        logger.info("Shutting down worker...")
        if self.poller: await self.poller.stop()
        if self.health_checker: await self.health_checker.stop()
        if self.notification_processor: await self.notification_processor.stop()
        # Close DB and Redis connections
        logger.info("Worker shutdown complete")

def main():
    manager = WorkerManager()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Handle SIGTERM and SIGINT for graceful shutdown
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(manager.shutdown()))

    try:
        loop.run_until_complete(manager.start())
    except KeyboardInterrupt:
        loop.run_until_complete(manager.shutdown())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
```

### 7. Worker Health Endpoint:
Add a simple health check for the worker process. Create a tiny FastAPI/aiohttp server on a separate port (e.g., 8001):
- GET /worker/health -> {"status": "ok", "poller_running": true, "devices_connected": 3, "uptime_seconds": 1234}


### 8. Docker Integration:
Update docker-compose.yml to add worker service:
```yaml
worker:
  build:
    context: ./backend
    dockerfile: Dockerfile
  command: python -m worker.main
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - FERNET_KEY=${FERNET_KEY}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - LOG_LEVEL=${LOG_LEVEL}
  depends_on:
    - db
    - redis
  networks:
    - attendx-network
  restart: unless-stopped
```


### 9. Metrics & Logging:
- Log every event processed: student_name, event_type, device_id, processing_time_ms
- Log device health changes: device went offline/online
- Track metrics in Redis:
  - `metrics:events:processed:{date}` — daily event count (INCR)
  - `metrics:events:errors:{date}` — daily error count
  - `metrics:devices:online` — current online device count


### 10. Tests (backend/tests/test_worker/):

**test_hikvision_client.py:**
- Mock httpx responses for ISAPI endpoints
- Test get_device_info() parses XML correctly
- Test add_user() sends correct XML
- Test get_events() handles pagination
- Test register_face() validates image size
- Test retry logic on connection error
- Test check_online() returns True/False

**test_event_poller.py:**
- Test _process_event() deduplicates events
- Test _process_event() creates attendance_log
- Test _process_event() publishes to Redis notification queue

**test_xml_helpers.py:**
- Test parse_xml_response() with sample Hikvision XML
- Test extract_events_from_xml() extracts correct fields
- Test build_xml() generates valid XML

**test_notification_processor.py:**
- Test format_attendance_message() for entry/exit
- Test _deliver_webhook() sends correct headers and HMAC signature


### 11. Update backend dependencies (pyproject.toml):
Add if not already present:
- Pillow >= 10.0  (image processing for face registration)
- tenacity >= 8.0  (retry logic)

Make sure all components integrate properly with the existing codebase from Phase 2. Use the same database models, config, and logging setup. No circular imports.

After completing, verify:
1. Worker starts without errors: python -m worker.main
2. All new tests pass: pytest tests/test_worker/ -v
3. No import errors or circular dependencies
```

Phase 4

This is Phase 4 of "AttendX" — Face Recognition Attendance Platform. Phases 1-3 are complete (project setup, backend core, hikvision worker). Now implement the REST API layer fully with all features.

Read the existing codebase first — models, schemas, services, repositories are already implemented. This phase focuses on making all API endpoints production-ready with proper validation, pagination, filtering, sorting, rate limiting, and documentation.

## TASK: Implement REST API (Phase 4)

### 1. Auth Endpoints (app/api/v1/auth.py) — Full Implementation:

**POST /api/v1/auth/login**
```python
@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT tokens.
    - Find user by username
    - Verify password (bcrypt)
    - Check is_active
    - Update last_login_at
    - Generate access_token + refresh_token
    - Create audit_log entry (action="login")
    - Return tokens with expires_in
    - On failure: raise AuthenticationException, log failed attempt
    - Brute force protection: track failed attempts in Redis
      key: f"auth:failed:{username}", increment, if > 5 → lock for 15 min
    """
```

**POST /api/v1/auth/refresh**
```python
@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.
    - Verify refresh_token (decode JWT, check exp)
    - Check token not blacklisted (Redis)
    - Generate new access_token (keep same refresh_token)
    - Return new tokens
    """
```

**POST /api/v1/auth/logout**
```python
@router.post("/logout", response_model=SuccessResponse[dict])
async def logout(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(extract_token)  # extract raw token from header
):
    """
    Logout and blacklist current token.
    - Extract JTI from token
    - Add to Redis blacklist with TTL = remaining token lifetime
    - Create audit_log entry (action="logout")
    - Return {"message": "Successfully logged out"}
    """
```

**GET /api/v1/auth/me**
```python
@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Return current authenticated user info."""
```

**POST /api/v1/auth/change-password**
```python
@router.post("/change-password", response_model=SuccessResponse[dict])
async def change_password(
    data: ChangePasswordRequest,  # old_password, new_password
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password.
    - Verify old_password
    - Hash new_password
    - Update user
    - Blacklist all existing tokens for this user (Redis: delete all keys matching f"token:{user_id}:*")
    - Create audit_log entry
    """
```

**Add to schemas/auth.py:**
- ChangePasswordRequest: old_password: str, new_password: str (min 8 chars)
- Add validator: new_password must contain at least 1 uppercase, 1 lowercase, 1 digit

**Helper function — extract_token dependency:**
```python
async def extract_token(authorization: str = Header(...)) -> str:
    """Extract Bearer token from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise AuthenticationException("Invalid authorization header")
    return authorization[7:]
```


### 2. Students Endpoints (app/api/v1/students.py) — Full Implementation:

**GET /api/v1/students**
```python
@router.get("", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    class_name: str | None = Query(None, description="Filter by class name"),
    search: str | None = Query(None, description="Search by name"),
    is_active: bool = Query(True, description="Filter by active status"),
    sort: str = Query("-created_at", description="Sort field. Prefix '-' for desc. Options: name, class_name, created_at"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List students with pagination, filtering, sorting.
    - Parse sort parameter: if starts with '-', order desc
    - Apply filters: class_name, search (ILIKE on name), is_active
    - Calculate offset = (page - 1) * per_page
    - Return PaginatedResponse with pagination info
    """
```

**POST /api/v1/students**
```python
@router.post("", response_model=SuccessResponse[StudentResponse], status_code=201)
async def create_student(
    data: StudentCreate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new student.
    - Check duplicate: external_id and employee_no must be unique
    - If employee_no not provided, auto-generate: "ATX-{sequential_number:06d}"
    - Create student
    - Create audit_log entry
    - Return created student
    """
```

**GET /api/v1/students/{student_id}**
```python
@router.get("/{student_id}", response_model=SuccessResponse[StudentResponse])
async def get_student(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single student by ID. Raise 404 if not found."""
```

**PUT /api/v1/students/{student_id}**
```python
@router.put("/{student_id}", response_model=SuccessResponse[StudentResponse])
async def update_student(
    student_id: UUID,
    data: StudentUpdate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student.
    - Only update provided fields (exclude_unset=True)
    - Check uniqueness if external_id or employee_no changed
    - Create audit_log entry with changed fields
    - Return updated student
    """
```

**DELETE /api/v1/students/{student_id}**
```python
@router.delete("/{student_id}", response_model=SuccessResponse[dict])
async def delete_student(
    student_id: UUID,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete student (is_active=False).
    - Do NOT hard delete — keep for audit trail
    - Create audit_log entry
    - Return {"message": "Student deactivated"}
    """
```

**POST /api/v1/students/{student_id}/face**
```python
@router.post("/{student_id}/face", response_model=SuccessResponse[StudentResponse])
async def upload_face(
    student_id: UUID,
    file: UploadFile = File(..., description="Face image (JPEG/PNG, max 5MB)"),
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload face image for student.
    - Validate file type: image/jpeg or image/png only
    - Validate file size: max 5MB
    - Save to disk: /data/faces/{student_id}.jpg
    - Convert to JPEG if PNG
    - Update student: face_image_path, face_registered=True
    - Queue face sync to terminals (publish to Redis: "worker:face_sync" channel)
    - Return updated student
    """
```

**POST /api/v1/students/import**
```python
@router.post("/import", response_model=SuccessResponse[StudentImportResponse])
async def import_students(
    file: UploadFile = File(..., description="Excel file (.xlsx)"),
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk import students from Excel.
    - Validate file type: .xlsx only
    - Parse with openpyxl
    - Expected columns: name, class_name, parent_phone, external_id (optional), phone (optional)
    - For each row:
      - Validate required fields
      - Auto-generate employee_no if not provided
      - If external_id exists → update, else → create
    - Return: {total: int, created: int, updated: int, errors: [{row: int, message: str}]}
    - Wrap in transaction: if critical errors, rollback all
    """
```

**GET /api/v1/students/export**
```python
@router.get("/export")
async def export_students(
    class_name: str | None = Query(None),
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Export students to Excel/CSV.
    - Generate file using openpyxl (xlsx) or csv module
    - Columns: name, class_name, phone, parent_phone, external_id, employee_no, face_registered, is_active
    - Return StreamingResponse with proper content-type and filename header
    """
```

**IMPORTANT:** The /import and /export routes must be registered BEFORE /{student_id} route to avoid path conflicts.


### 3. Attendance Endpoints (app/api/v1/attendance.py) — Full Implementation:

**GET /api/v1/attendance**
```python
@router.get("", response_model=PaginatedResponse[AttendanceResponse])
async def list_attendance(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    date_from: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    class_name: str | None = Query(None),
    student_id: UUID | None = Query(None),
    event_type: str | None = Query(None, regex="^(entry|exit)$"),
    sort: str = Query("-event_time"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List attendance logs with comprehensive filtering.
    - Join with students table to include student_name, class_name
    - Join with devices table to include device_name
    - Apply all filters
    - Default: today's records if no date specified
    """
```

**GET /api/v1/attendance/today**
```python
@router.get("/today", response_model=SuccessResponse[list[AttendanceResponse]])
async def today_attendance(
    class_name: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get today's attendance.
    - Filter: event_time >= today 00:00:00
    - Optional class_name filter
    - Join student and device info
    - Order by event_time desc
    """
```

**GET /api/v1/attendance/stats**
```python
@router.get("/stats", response_model=SuccessResponse[AttendanceStats])
async def attendance_stats(
    date: date | None = Query(None, description="Date for stats (default: today)"),
    class_name: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get attendance statistics.
    Return:
    - total_students: total active students (filtered by class if provided)
    - present_today: students who have at least one entry event today
    - absent_today: total - present
    - attendance_percentage: (present / total) * 100
    - by_class: {class_name: {total, present, absent, percentage}}
    """
```

**GET /api/v1/attendance/weekly**
```python
@router.get("/weekly", response_model=SuccessResponse[list[DailyAttendance]])
async def weekly_stats(
    start_date: date | None = Query(None, description="Week start (default: this Monday)"),
    class_name: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily attendance for a week (7 days).
    Return list of: {date, present, absent, percentage}
    """
```

**GET /api/v1/attendance/report**
```python
@router.get("/report")
async def attendance_report(
    date_from: date = Query(..., description="Report start date"),
    date_to: date = Query(..., description="Report end date"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", regex="^(xlsx|pdf)$"),
    current_user: User = Depends(require_role("superadmin", "admin", "teacher")),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate attendance report.
    - XLSX: Use openpyxl
      - Sheet 1: Summary (dates, total, present, absent, percentage per day)
      - Sheet 2: Details (each student, each day: present/absent)
    - PDF: Use reportlab or weasyprint
      - Header: AttendX Attendance Report, date range
      - Table: student name, class, daily attendance marks
      - Footer: statistics summary
    - Return StreamingResponse with proper headers
    """
```

**GET /api/v1/attendance/student/{student_id}**
```python
@router.get("/student/{student_id}", response_model=SuccessResponse[dict])
async def student_attendance(
    student_id: UUID,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get attendance history for a specific student.
    Return: {student: StudentResponse, records: list[AttendanceResponse], stats: {total_days, present_days, percentage}}
    """
```


### 4. Devices Endpoints (app/api/v1/devices.py) — Full Implementation:

**GET /api/v1/devices**
```python
@router.get("", response_model=SuccessResponse[list[DeviceResponse]])
async def list_devices(
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """List all devices. Include real-time status from Redis (online/offline, response_time)."""
```

**POST /api/v1/devices**
```python
@router.post("", response_model=SuccessResponse[DeviceResponse], status_code=201)
async def create_device(
    data: DeviceCreate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Add new device.
    - Encrypt password with Fernet before storing
    - Check duplicate IP address
    - Create audit_log entry
    - Publish to Redis: "worker:device_added" to notify worker to reload clients
    """
```

**PUT /api/v1/devices/{device_id}**
```python
@router.put("/{device_id}", response_model=SuccessResponse[DeviceResponse])
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update device.
    - If password provided, re-encrypt
    - Create audit_log entry
    - Publish to Redis: "worker:device_updated"
    """
```

**DELETE /api/v1/devices/{device_id}**
```python
@router.delete("/{device_id}", response_model=SuccessResponse[dict])
async def delete_device(
    device_id: int,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete device.
    - Hard delete (devices don't need soft delete)
    - Create audit_log
    - Publish: "worker:device_removed"
    """
```

**POST /api/v1/devices/{device_id}/sync**
```python
@router.post("/{device_id}/sync", response_model=SuccessResponse[dict])
async def sync_device(
    device_id: int,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger full sync for a device.
    - Publish to Redis: "worker:full_sync" with device_id
    - Return {"message": "Sync queued", "device_id": device_id}
    - Actual sync happens in worker process
    """
```

**GET /api/v1/devices/{device_id}/health**
```python
@router.get("/{device_id}/health", response_model=SuccessResponse[DeviceHealth])
async def device_health(
    device_id: int,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get device health status.
    - Read from Redis: device:{id}:online, device:{id}:response_time
    - Return DeviceHealth with real-time data
    """
```


### 5. Webhooks Endpoints (app/api/v1/webhooks.py) — Full Implementation:

**GET /api/v1/webhooks**
```python
@router.get("", response_model=SuccessResponse[list[WebhookResponse]])
async def list_webhooks(
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """List all webhooks (exclude secret from response)."""
```

**POST /api/v1/webhooks**
```python
@router.post("", response_model=SuccessResponse[WebhookResponse], status_code=201)
async def create_webhook(
    data: WebhookCreate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create webhook.
    - Auto-generate secret if not provided (secrets.token_urlsafe(32))
    - Validate URL format (must be https:// or http:// for dev)
    - Validate events list against allowed events:
      [attendance.entry, attendance.exit, student.created, student.updated, student.deleted,
       device.online, device.offline, face.registered]
    - Return webhook (show secret ONLY on creation, never again)
    """
```

**PUT /api/v1/webhooks/{webhook_id}**
```python
@router.put("/{webhook_id}", response_model=SuccessResponse[WebhookResponse])
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Update webhook. Cannot change secret (must delete and recreate)."""
```

**DELETE /api/v1/webhooks/{webhook_id}**
```python
@router.delete("/{webhook_id}", response_model=SuccessResponse[dict])
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Delete webhook and all associated logs."""
```

**GET /api/v1/webhooks/{webhook_id}/logs**
```python
@router.get("/{webhook_id}/logs", response_model=PaginatedResponse[WebhookLogResponse])
async def webhook_logs(
    webhook_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    success: bool | None = Query(None, description="Filter by success status"),
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get webhook delivery logs with pagination."""
```

**POST /api/v1/webhooks/{webhook_id}/test**
```python
@router.post("/{webhook_id}/test", response_model=SuccessResponse[dict])
async def test_webhook(
    webhook_id: UUID,
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Send test ping to webhook.
    - Send POST to webhook URL with:
      - Event: "webhook.test"
      - Payload: {"event": "webhook.test", "timestamp": "...", "message": "Test from AttendX"}
      - Proper HMAC signature
    - Log the delivery attempt
    - Return: {delivered: bool, status_code: int, response_time_ms: int}
    """
```


### 6. Reports Endpoints (app/api/v1/reports.py):

**GET /api/v1/reports/daily**
```python
@router.get("/daily")
async def daily_report(
    date: date = Query(default=None, description="Report date, default today"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", regex="^(xlsx|pdf)$"),
    current_user: User = Depends(require_role("superadmin", "admin", "teacher")),
    db: AsyncSession = Depends(get_db)
):
    """Generate daily attendance report."""
```

**GET /api/v1/reports/weekly**
```python
@router.get("/weekly")
async def weekly_report(
    start_date: date = Query(default=None, description="Week start date, default this Monday"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx"),
    current_user: User = Depends(require_role("superadmin", "admin", "teacher")),
    db: AsyncSession = Depends(get_db)
):
    """Generate weekly attendance report."""
```

**GET /api/v1/reports/monthly**
```python
@router.get("/monthly")
async def monthly_report(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    class_name: str | None = Query(None),
    format: str = Query("xlsx"),
    current_user: User = Depends(require_role("superadmin", "admin", "teacher")),
    db: AsyncSession = Depends(get_db)
):
    """Generate monthly attendance report with summary statistics."""
```


### 7. Rate Limiting Middleware (app/core/rate_limit.py):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"]
)

# Apply to specific endpoints:
# Public endpoints (login): "10/minute"
# Authenticated endpoints: "100/minute"  
# Export/Report endpoints: "10/minute" (heavy operations)
# Webhook test: "5/minute"
```

Add slowapi to dependencies. Register limiter in main.py.


### 8. Request/Response Middleware (app/core/middleware.py):

**RequestIDMiddleware:**
- Generate UUID for each request
- Add to response headers: X-Request-ID
- Store in contextvars for logging

**LoggingMiddleware:**
- Log: method, path, status_code, duration_ms, request_id
- Skip logging for /health endpoint
- Log request body for POST/PUT (mask sensitive fields: password, secret)

**CompressionMiddleware:**
- Add GZipMiddleware for responses > 1KB


### 9. API Key Authentication (app/api/v1/external.py):

Create separate router for external system access (via API key instead of JWT):

**GET /api/v1/external/students**
- Same as students list but authenticated via X-API-Key header
- Read-only access

**GET /api/v1/external/attendance/today**
- Today's attendance for external systems

**POST /api/v1/external/attendance/query**
- Query attendance with filters (for MBI-Chat, Kundalik integration)
- Body: {date_from, date_to, class_name, external_ids: list}

These endpoints use get_api_key dependency instead of JWT.


### 10. OpenAPI Documentation Enhancement:

Update main.py FastAPI config:
```python
app = FastAPI(
    title="AttendX API",
    description="""
    ## AttendX — Face Recognition Attendance Platform
    
    REST API for managing Hikvision terminals, students, and attendance monitoring.
    
    ### Authentication
    - **JWT Bearer**: For admin/teacher dashboard access
    - **API Key**: For external system integration (X-API-Key header)
    
    ### Rate Limits
    - Default: 100 requests/minute
    - Login: 10 requests/minute
    - Reports/Export: 10 requests/minute
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication & authorization"},
        {"name": "students", "description": "Student management"},
        {"name": "attendance", "description": "Attendance records & statistics"},
        {"name": "devices", "description": "Hikvision terminal management"},
        {"name": "webhooks", "description": "Webhook management & delivery"},
        {"name": "reports", "description": "Report generation (PDF/Excel)"},
        {"name": "external", "description": "External system API (API Key auth)"},
    ]
)
```

Tag all routers appropriately.


### 11. Postman Collection Export:

Create a script or endpoint that generates a Postman collection JSON:
- File: docs/postman_collection.json
- Include all endpoints with example requests/responses
- Include auth setup (Bearer token variable, API key variable)
- Include environment variables template


### 12. Error Code Reference:

Create app/core/error_codes.py:
```python
class ErrorCode:
    # Auth
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Students
    STUDENT_NOT_FOUND = "STUDENT_NOT_FOUND"
    STUDENT_DUPLICATE_EXTERNAL_ID = "STUDENT_DUPLICATE_EXTERNAL_ID"
    STUDENT_DUPLICATE_EMPLOYEE_NO = "STUDENT_DUPLICATE_EMPLOYEE_NO"
    INVALID_FACE_IMAGE = "INVALID_FACE_IMAGE"
    IMPORT_VALIDATION_ERROR = "IMPORT_VALIDATION_ERROR"
    
    # Attendance
    ATTENDANCE_NOT_FOUND = "ATTENDANCE_NOT_FOUND"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    
    # Devices
    DEVICE_NOT_FOUND = "DEVICE_NOT_FOUND"
    DEVICE_DUPLICATE_IP = "DEVICE_DUPLICATE_IP"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    DEVICE_SYNC_FAILED = "DEVICE_SYNC_FAILED"
    
    # Webhooks
    WEBHOOK_NOT_FOUND = "WEBHOOK_NOT_FOUND"
    WEBHOOK_DELIVERY_FAILED = "WEBHOOK_DELIVERY_FAILED"
    INVALID_WEBHOOK_URL = "INVALID_WEBHOOK_URL"
    INVALID_WEBHOOK_EVENT = "INVALID_WEBHOOK_EVENT"
    
    # General
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

Use these codes in all exception raises consistently.


### 13. Update Router (app/api/v1/router.py):
```python
from fastapi import APIRouter
from app.api.v1 import auth, students, attendance, devices, webhooks, reports, external

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(external.router, prefix="/external", tags=["external"])
```


### 14. Additional Dependencies (pyproject.toml):
Add if not present:
- slowapi (rate limiting)
- openpyxl (Excel import/export)
- reportlab OR weasyprint (PDF generation)
- python-multipart (file uploads)


### 15. API Tests (backend/tests/test_api/):

**test_auth_api.py:**
- Test login success → 200 + tokens
- Test login invalid password → 401 + INVALID_CREDENTIALS
- Test login locked account (>5 failures) → 401 + ACCOUNT_LOCKED
- Test refresh token → 200 + new access token
- Test refresh with expired token → 401
- Test logout → 200, then use same token → 401
- Test /me with valid token → 200
- Test /me without token → 401
- Test change password → 200

**test_students_api.py:**
- Test CRUD full cycle: create → get → update → list → delete
- Test create duplicate external_id → 409
- Test list with pagination → correct page/per_page/total
- Test list with class_name filter → only matching students
- Test list with search → name ILIKE match
- Test import Excel → correct created/updated/errors count
- Test export → returns xlsx file with correct content-type
- Test face upload → file saved, face_registered=True
- Test face upload invalid format → 422
- Test unauthorized access (teacher tries to create) → 403

**test_attendance_api.py:**
- Test list with date filter
- Test today endpoint
- Test stats calculation (present/absent/percentage)
- Test weekly stats
- Test student-specific attendance

**test_devices_api.py:**
- Test CRUD full cycle
- Test duplicate IP → 409
- Test health endpoint (mock Redis data)
- Test sync trigger → returns queued message

**test_webhooks_api.py:**
- Test CRUD full cycle
- Test secret auto-generation on create
- Test invalid event type → 422
- Test webhook test ping
- Test delivery logs pagination

**test_external_api.py:**
- Test with valid API key → 200
- Test without API key → 401
- Test with invalid API key → 401

After completing, verify:
1. All tests pass: pytest tests/ -v
2. App starts: uvicorn app.main:app --reload
3. Visit /docs → all endpoints visible with correct tags
4. Visit /redoc → detailed documentation
5. Test login via /docs → get token → use in other endpoints
```

Phase 5

This is Phase 5 of "AttendX" — Face Recognition Attendance Platform. Phases 1-4 are complete (setup, backend core, hikvision worker, REST API). Now implement the Webhook System as a robust, production-ready event delivery engine.

Read the existing codebase first — webhook models, schemas, API endpoints, and notification processor already exist from previous phases. This phase focuses on building the complete webhook engine with reliable delivery, retry logic, circuit breaker, signature verification, and comprehensive logging.

## TASK: Implement Webhook System (Phase 5)

### 1. Webhook Engine (app/services/webhook_engine.py):

This is the core engine responsible for delivering webhooks reliably.

```python
import hmac
import hashlib
import json
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Any

class WebhookEngine:
    """
    Production-ready webhook delivery engine.
    Features: HMAC signing, async delivery, retry with exponential backoff,
    circuit breaker, delivery logging, batch processing.
    """

    RETRY_DELAYS = [10, 60, 300]  # seconds: 10s, 1min, 5min
    DELIVERY_TIMEOUT = 30  # seconds
    MAX_PAYLOAD_SIZE = 256 * 1024  # 256KB max payload

    def __init__(self, db_session_factory, redis_client):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.http_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Create shared HTTP client for all webhook deliveries."""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=self.DELIVERY_TIMEOUT, write=10.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
            follow_redirects=False,  # Don't follow redirects for security
            verify=True
        )

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.aclose()

    async def dispatch_event(self, event_type: str, payload: dict) -> dict:
        """
        Main entry point: dispatch an event to all subscribed webhooks.
        
        Args:
            event_type: e.g., "attendance.entry", "student.created", "device.offline"
            payload: Event data dict
            
        Returns:
            {total: int, delivered: int, failed: int, skipped: int, details: list}
        """
        # 1. Query all active webhooks subscribed to this event_type
        # 2. For each webhook:
        #    a. Check circuit breaker — if open, skip (increment skipped)
        #    b. Build delivery payload with metadata
        #    c. Generate HMAC signature
        #    d. Attempt delivery
        #    e. Log result
        #    f. If failed, queue for retry
        # 3. Return summary

    async def deliver(self, webhook, event_type: str, payload: dict) -> WebhookDeliveryResult:
        """
        Deliver a single webhook with full lifecycle.
        
        Returns WebhookDeliveryResult with all details.
        """
        delivery_id = str(uuid4())
        
        # Build the full payload
        full_payload = {
            "event": event_type,
            "delivery_id": delivery_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": payload
        }
        
        payload_json = json.dumps(full_payload, default=str, ensure_ascii=False)
        
        # Check payload size
        if len(payload_json.encode()) > self.MAX_PAYLOAD_SIZE:
            # Truncate or reject
            pass
        
        # Generate HMAC-SHA256 signature
        signature = self._generate_signature(webhook.secret, payload_json)
        
        # Build headers
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "AttendX-Webhook/1.0",
            "X-AttendX-Event": event_type,
            "X-AttendX-Delivery": delivery_id,
            "X-AttendX-Signature": f"sha256={signature}",
            "X-AttendX-Timestamp": str(int(datetime.utcnow().timestamp())),
        }
        
        # Attempt delivery
        start_time = time.monotonic()
        try:
            response = await self.http_client.post(
                str(webhook.url),
                content=payload_json,
                headers=headers
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)
            
            success = 200 <= response.status_code < 300
            
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=success,
                status_code=response.status_code,
                response_body=response.text[:1000],  # truncate response
                duration_ms=duration_ms,
                attempt=1
            )
        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                response_body="Timeout",
                duration_ms=duration_ms,
                error="Connection timeout",
                attempt=1
            )
        except httpx.ConnectError as e:
            return WebhookDeliveryResult(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                success=False,
                status_code=0,
                response_body="",
                duration_ms=0,
                error=f"Connection error: {str(e)[:200]}",
                attempt=1
            )

    @staticmethod
    def _generate_signature(secret: str, payload: str) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_signature(secret: str, payload: str, signature: str) -> bool:
        """
        Verify HMAC-SHA256 signature (for documentation/helper purposes).
        Receivers should use this logic to verify incoming webhooks.
        """
        expected = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
```


### 2. Retry System (app/services/webhook_retry.py):

```python
class WebhookRetryManager:
    """
    Manages failed webhook delivery retries using Redis sorted sets.
    
    Strategy: Exponential backoff with 3 attempts
    - Attempt 1: Immediate (in dispatch_event)
    - Attempt 2: After 10 seconds
    - Attempt 3: After 60 seconds  
    - Attempt 4: After 300 seconds (5 min) — final attempt
    
    After all retries exhausted → mark as permanently failed, alert admin.
    """

    RETRY_QUEUE_KEY = "webhook:retry:queue"  # Redis sorted set (score = retry_at timestamp)
    MAX_RETRIES = 3
    RETRY_DELAYS = [10, 60, 300]  # seconds

    def __init__(self, webhook_engine: WebhookEngine, db_session_factory, redis_client):
        self.engine = webhook_engine
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.running = False

    async def queue_retry(self, webhook_id: str, event_type: str, payload: dict, attempt: int) -> None:
        """
        Queue a failed delivery for retry.
        Store in Redis sorted set with score = unix timestamp of next retry.
        """
        if attempt > self.MAX_RETRIES:
            # All retries exhausted — log permanent failure
            await self._handle_permanent_failure(webhook_id, event_type, payload)
            return

        delay = self.RETRY_DELAYS[attempt - 1] if attempt <= len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
        retry_at = datetime.utcnow().timestamp() + delay

        retry_data = json.dumps({
            "webhook_id": str(webhook_id),
            "event_type": event_type,
            "payload": payload,
            "attempt": attempt + 1,
            "original_timestamp": datetime.utcnow().isoformat(),
            "retry_id": str(uuid4())
        })

        await self.redis.zadd(self.RETRY_QUEUE_KEY, {retry_data: retry_at})
        logger.info("Webhook retry queued",
                     webhook_id=str(webhook_id),
                     attempt=attempt + 1,
                     retry_in_seconds=delay)

    async def start_retry_processor(self) -> None:
        """
        Background loop that processes retry queue.
        Checks every 5 seconds for items ready to retry.
        """
        self.running = True
        while self.running:
            try:
                await self._process_pending_retries()
            except Exception as e:
                logger.error("Retry processor error", error=str(e))
            await asyncio.sleep(5)

    async def stop(self) -> None:
        self.running = False

    async def _process_pending_retries(self) -> None:
        """Process all retries that are due."""
        now = datetime.utcnow().timestamp()
        
        # Get all items with score <= now (ready to retry)
        items = await self.redis.zrangebyscore(
            self.RETRY_QUEUE_KEY, "-inf", str(now), start=0, num=50
        )

        for item in items:
            # Remove from queue first (prevent double processing)
            removed = await self.redis.zrem(self.RETRY_QUEUE_KEY, item)
            if not removed:
                continue  # Another worker already took it

            retry_data = json.loads(item)
            await self._execute_retry(retry_data)

    async def _execute_retry(self, retry_data: dict) -> None:
        """Execute a single retry attempt."""
        webhook_id = retry_data["webhook_id"]
        event_type = retry_data["event_type"]
        payload = retry_data["payload"]
        attempt = retry_data["attempt"]

        async with self.db_session_factory() as session:
            # Get webhook from DB
            webhook = await session.get(Webhook, webhook_id)
            if not webhook or not webhook.is_active:
                logger.info("Webhook no longer active, skipping retry", webhook_id=webhook_id)
                return

            # Attempt delivery
            result = await self.engine.deliver(webhook, event_type, payload)
            result.attempt = attempt

            # Log the attempt
            await self._log_delivery(session, result)
            await session.commit()

            if not result.success:
                # Queue next retry if attempts remain
                await self.queue_retry(webhook_id, event_type, payload, attempt)

    async def _handle_permanent_failure(self, webhook_id: str, event_type: str, payload: dict) -> None:
        """Handle permanently failed webhook delivery."""
        logger.error("Webhook delivery permanently failed",
                     webhook_id=webhook_id,
                     event_type=event_type)
        
        # Store in dead letter queue
        dead_letter = json.dumps({
            "webhook_id": webhook_id,
            "event_type": event_type,
            "payload": payload,
            "failed_at": datetime.utcnow().isoformat(),
            "max_retries_exceeded": True
        })
        await self.redis.lpush("webhook:dead_letter", dead_letter)
        
        # Keep only last 1000 dead letters
        await self.redis.ltrim("webhook:dead_letter", 0, 999)

    async def get_retry_queue_size(self) -> int:
        """Get number of items in retry queue."""
        return await self.redis.zcard(self.RETRY_QUEUE_KEY)

    async def get_dead_letter_count(self) -> int:
        """Get number of permanently failed deliveries."""
        return await self.redis.llen("webhook:dead_letter")

    async def retry_dead_letter(self, index: int) -> bool:
        """Manually retry a dead letter item (admin action)."""
        item = await self.redis.lindex("webhook:dead_letter", index)
        if not item:
            return False
        data = json.loads(item)
        await self.queue_retry(data["webhook_id"], data["event_type"], data["payload"], 0)
        await self.redis.lrem("webhook:dead_letter", 1, item)
        return True
```


### 3. Circuit Breaker (app/services/webhook_circuit_breaker.py):

```python
class CircuitBreaker:
    """
    Circuit breaker pattern for webhook endpoints.
    
    States:
    - CLOSED: Normal operation, deliveries proceed
    - OPEN: Too many failures, deliveries skipped (fast-fail)
    - HALF_OPEN: Testing if endpoint recovered
    
    Thresholds:
    - Open after 5 consecutive failures
    - Stay open for 60 seconds
    - Half-open: allow 1 test request
    - If test succeeds → CLOSED
    - If test fails → OPEN again (reset timer)
    """

    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60  # seconds
    REDIS_PREFIX = "webhook:circuit:"

    def __init__(self, redis_client):
        self.redis = redis_client

    async def can_deliver(self, webhook_id: str) -> bool:
        """Check if delivery is allowed for this webhook."""
        state = await self._get_state(webhook_id)
        
        if state == "closed":
            return True
        elif state == "open":
            # Check if recovery timeout has passed
            opened_at = await self.redis.get(f"{self.REDIS_PREFIX}{webhook_id}:opened_at")
            if opened_at:
                elapsed = datetime.utcnow().timestamp() - float(opened_at)
                if elapsed >= self.RECOVERY_TIMEOUT:
                    # Transition to half-open
                    await self._set_state(webhook_id, "half_open")
                    return True  # Allow one test request
            return False
        elif state == "half_open":
            return True  # Allow test request
        
        return True  # Default: allow

    async def record_success(self, webhook_id: str) -> None:
        """Record successful delivery."""
        state = await self._get_state(webhook_id)
        
        if state == "half_open":
            # Recovery successful → close circuit
            await self._set_state(webhook_id, "closed")
            await self.redis.delete(f"{self.REDIS_PREFIX}{webhook_id}:failures")
            logger.info("Circuit breaker closed (recovered)", webhook_id=webhook_id)
        
        # Reset failure counter on success
        await self.redis.delete(f"{self.REDIS_PREFIX}{webhook_id}:failures")

    async def record_failure(self, webhook_id: str) -> None:
        """Record failed delivery."""
        state = await self._get_state(webhook_id)
        
        if state == "half_open":
            # Test failed → reopen circuit
            await self._set_state(webhook_id, "open")
            await self.redis.set(
                f"{self.REDIS_PREFIX}{webhook_id}:opened_at",
                str(datetime.utcnow().timestamp())
            )
            logger.warning("Circuit breaker reopened", webhook_id=webhook_id)
            return

        # Increment failure counter
        failures = await self.redis.incr(f"{self.REDIS_PREFIX}{webhook_id}:failures")
        
        if failures >= self.FAILURE_THRESHOLD:
            # Open the circuit
            await self._set_state(webhook_id, "open")
            await self.redis.set(
                f"{self.REDIS_PREFIX}{webhook_id}:opened_at",
                str(datetime.utcnow().timestamp())
            )
            logger.warning("Circuit breaker opened",
                         webhook_id=webhook_id,
                         consecutive_failures=failures)

    async def get_status(self, webhook_id: str) -> dict:
        """Get circuit breaker status for a webhook."""
        state = await self._get_state(webhook_id)
        failures = await self.redis.get(f"{self.REDIS_PREFIX}{webhook_id}:failures")
        opened_at = await self.redis.get(f"{self.REDIS_PREFIX}{webhook_id}:opened_at")
        
        return {
            "webhook_id": webhook_id,
            "state": state,
            "consecutive_failures": int(failures) if failures else 0,
            "opened_at": opened_at.decode() if opened_at else None,
            "recovery_timeout_seconds": self.RECOVERY_TIMEOUT
        }

    async def reset(self, webhook_id: str) -> None:
        """Manually reset circuit breaker (admin action)."""
        await self._set_state(webhook_id, "closed")
        await self.redis.delete(f"{self.REDIS_PREFIX}{webhook_id}:failures")
        await self.redis.delete(f"{self.REDIS_PREFIX}{webhook_id}:opened_at")

    async def _get_state(self, webhook_id: str) -> str:
        state = await self.redis.get(f"{self.REDIS_PREFIX}{webhook_id}:state")
        return state.decode() if state else "closed"

    async def _set_state(self, webhook_id: str, state: str) -> None:
        await self.redis.set(f"{self.REDIS_PREFIX}{webhook_id}:state", state)
```


### 4. Webhook Delivery Logger (app/services/webhook_logger.py):

```python
class WebhookDeliveryLogger:
    """Logs all webhook delivery attempts to database and provides query methods."""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    async def log_delivery(self, session: AsyncSession, result: WebhookDeliveryResult) -> WebhookLog:
        """Save delivery result to webhook_logs table."""
        log = WebhookLog(
            webhook_id=result.webhook_id,
            event_type=result.event_type,
            payload=result.payload,
            response_status=result.status_code,
            response_body=result.response_body[:2000] if result.response_body else None,
            attempts=result.attempt,
            success=result.success,
            delivery_id=result.delivery_id,
            duration_ms=result.duration_ms,
            error_message=result.error
        )
        session.add(log)
        return log

    async def get_delivery_stats(self, webhook_id: UUID | None = None, days: int = 7) -> dict:
        """
        Get webhook delivery statistics.
        Return:
        {
            total_deliveries: int,
            successful: int,
            failed: int,
            success_rate: float,  # percentage
            avg_response_time_ms: float,
            by_event_type: {event_type: {total, success, failed}},
            by_day: [{date, total, success, failed}]
        }
        """

    async def get_recent_failures(self, limit: int = 20) -> list[WebhookLog]:
        """Get most recent failed deliveries across all webhooks."""

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete webhook logs older than specified days. Return deleted count."""
```


### 5. Event Trigger Integration (app/services/webhook_events.py):

This ties the webhook engine into the rest of the application — every relevant action triggers the appropriate webhook event.

```python
class WebhookEventManager:
    """
    Central event dispatcher — called by services when events occur.
    Maps application events to webhook deliveries.
    """

    def __init__(self, webhook_engine: WebhookEngine):
        self.engine = webhook_engine

    async def on_attendance_entry(self, student, device, event_time: datetime) -> None:
        """Triggered when a student enters (from Hikvision worker)."""
        await self.engine.dispatch_event("attendance.entry", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "student_name": student.name,
            "class_name": student.class_name,
            "event_time": event_time.isoformat(),
            "device_name": device.name if device else None,
            "device_id": device.id if device else None,
            "verify_mode": "face"
        })

    async def on_attendance_exit(self, student, device, event_time: datetime) -> None:
        """Triggered when a student exits."""
        await self.engine.dispatch_event("attendance.exit", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "student_name": student.name,
            "class_name": student.class_name,
            "event_time": event_time.isoformat(),
            "device_name": device.name if device else None,
            "device_id": device.id if device else None,
            "verify_mode": "face"
        })

    async def on_student_created(self, student) -> None:
        """Triggered when a new student is created via API."""
        await self.engine.dispatch_event("student.created", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "name": student.name,
            "class_name": student.class_name,
            "parent_phone": student.parent_phone
        })

    async def on_student_updated(self, student, changed_fields: list[str]) -> None:
        """Triggered when student info is updated."""
        await self.engine.dispatch_event("student.updated", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "name": student.name,
            "class_name": student.class_name,
            "changed_fields": changed_fields
        })

    async def on_student_deleted(self, student) -> None:
        """Triggered when student is deactivated/deleted."""
        await self.engine.dispatch_event("student.deleted", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "name": student.name
        })

    async def on_device_online(self, device) -> None:
        """Triggered when terminal comes online."""
        await self.engine.dispatch_event("device.online", {
            "device_id": device.id,
            "device_name": device.name,
            "ip_address": device.ip_address,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def on_device_offline(self, device) -> None:
        """Triggered when terminal goes offline."""
        await self.engine.dispatch_event("device.offline", {
            "device_id": device.id,
            "device_name": device.name,
            "ip_address": device.ip_address,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def on_face_registered(self, student, device_count: int) -> None:
        """Triggered when face is registered on terminals."""
        await self.engine.dispatch_event("face.registered", {
            "student_id": str(student.id),
            "external_id": student.external_id,
            "employee_no": student.employee_no,
            "name": student.name,
            "devices_synced": device_count,
            "timestamp": datetime.utcnow().isoformat()
        })
```


### 6. Integrate Webhook Events into Existing Services:

Update the following services to trigger webhook events:

**app/services/student_service.py:**
- After create_student() → call webhook_events.on_student_created(student)
- After update_student() → call webhook_events.on_student_updated(student, changed_fields)
- After delete_student() → call webhook_events.on_student_deleted(student)
- After register_face() → call webhook_events.on_face_registered(student, device_count)

**worker/hikvision/poller.py (EventPoller._process_event):**
- After recording attendance entry → call webhook_events.on_attendance_entry(student, device, event_time)
- After recording attendance exit → call webhook_events.on_attendance_exit(student, device, event_time)

**worker/hikvision/health.py (HealthChecker._check_device):**
- On device went offline → call webhook_events.on_device_offline(device)
- On device came online → call webhook_events.on_device_online(device)

Use fire-and-forget pattern: `asyncio.create_task(webhook_events.on_xxx())` so webhook delivery doesn't block the main flow.


### 7. Data Models for Webhook Delivery (app/schemas/webhook_delivery.py):

```python
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime

@dataclass
class WebhookDeliveryResult:
    delivery_id: str
    webhook_id: UUID
    event_type: str
    success: bool
    status_code: int
    response_body: str = ""
    duration_ms: int = 0
    error: str | None = None
    attempt: int = 1
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

Update WebhookLog model if needed — add columns:
- delivery_id: VARCHAR(100), nullable (for tracking across retries)
- duration_ms: Integer, nullable
- error_message: Text, nullable


### 8. Webhook Admin API Enhancements (update app/api/v1/webhooks.py):

Add these additional endpoints:

**GET /api/v1/webhooks/stats**
```python
@router.get("/stats", response_model=SuccessResponse[dict])
async def webhook_stats(current_user = Depends(require_role("superadmin", "admin")), db = Depends(get_db)):
    """
    Get overall webhook system statistics.
    Return: {
        total_webhooks: int,
        active_webhooks: int,
        total_deliveries_today: int,
        success_rate_today: float,
        retry_queue_size: int,
        dead_letter_count: int,
        circuit_breakers: [{webhook_id, state, failures}]
    }
    """
```

**POST /api/v1/webhooks/{webhook_id}/retry**
```python
@router.post("/{webhook_id}/retry", response_model=SuccessResponse[dict])
async def manual_retry(
    webhook_id: UUID,
    log_id: UUID = Query(..., description="Webhook log ID to retry"),
    current_user = Depends(require_role("superadmin", "admin")),
    db = Depends(get_db)
):
    """Manually retry a specific failed delivery."""
```

**GET /api/v1/webhooks/{webhook_id}/circuit-breaker**
```python
@router.get("/{webhook_id}/circuit-breaker", response_model=SuccessResponse[dict])
async def circuit_breaker_status(
    webhook_id: UUID,
    current_user = Depends(require_role("superadmin", "admin"))
):
    """Get circuit breaker status for a webhook."""
```

**POST /api/v1/webhooks/{webhook_id}/circuit-breaker/reset**
```python
@router.post("/{webhook_id}/circuit-breaker/reset", response_model=SuccessResponse[dict])
async def reset_circuit_breaker(
    webhook_id: UUID,
    current_user = Depends(require_role("superadmin", "admin"))
):
    """Manually reset circuit breaker for a webhook."""
```

**GET /api/v1/webhooks/dead-letter**
```python
@router.get("/dead-letter", response_model=SuccessResponse[list[dict]])
async def dead_letter_queue(
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(require_role("superadmin", "admin"))
):
    """View dead letter queue (permanently failed deliveries)."""
```

**POST /api/v1/webhooks/dead-letter/{index}/retry**
```python
@router.post("/dead-letter/{index}/retry", response_model=SuccessResponse[dict])
async def retry_dead_letter(
    index: int,
    current_user = Depends(require_role("superadmin", "admin"))
):
    """Retry a specific dead letter item."""
```


### 9. Webhook Signature Verification Documentation (docs/webhook-verification.md):

Create documentation file showing how receiving systems should verify webhook signatures:

```markdown
# AttendX Webhook Signature Verification

## How it works
Every webhook delivery includes an HMAC-SHA256 signature in the X-AttendX-Signature header.

## Verification examples

### Python
import hmac, hashlib
def verify(secret, payload_body, signature_header):
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)

### Node.js
const crypto = require('crypto');
function verify(secret, payloadBody, signatureHeader) {
    const expected = crypto.createHmac('sha256', secret).update(payloadBody).digest('hex');
    return crypto.timingSafeEqual(Buffer.from(`sha256=${expected}`), Buffer.from(signatureHeader));
}

### PHP
function verify($secret, $payloadBody, $signatureHeader) {
    $expected = 'sha256=' . hash_hmac('sha256', $payloadBody, $secret);
    return hash_equals($expected, $signatureHeader);
}
```


### 10. Webhook Cleanup Cron (app/services/webhook_cleanup.py):

```python
class WebhookCleanup:
    """Periodic cleanup of old webhook logs and dead letters."""

    async def cleanup_logs(self, db_session_factory, days: int = 30) -> int:
        """Delete webhook_logs older than X days. Run daily via cron/scheduler."""
        async with db_session_factory() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                delete(WebhookLog).where(WebhookLog.created_at < cutoff)
            )
            await session.commit()
            deleted = result.rowcount
            logger.info(f"Cleaned up {deleted} old webhook logs")
            return deleted

    async def cleanup_dead_letters(self, redis_client, max_items: int = 1000) -> None:
        """Trim dead letter queue to max items."""
        await redis_client.ltrim("webhook:dead_letter", 0, max_items - 1)
```


### 11. Tests (backend/tests/test_webhooks/):

**test_webhook_engine.py:**
- Test dispatch_event() finds correct subscribed webhooks
- Test deliver() sends correct headers and HMAC signature
- Test deliver() handles timeout gracefully
- Test deliver() handles connection error
- Test _generate_signature() produces correct HMAC
- Test verify_signature() validates correctly
- Test payload size limit enforcement

**test_webhook_retry.py:**
- Test queue_retry() adds to Redis sorted set with correct score
- Test _process_pending_retries() processes due items
- Test retry escalation: attempt 1 → 10s, attempt 2 → 60s, attempt 3 → 300s
- Test max retries exceeded → moves to dead letter queue
- Test retry_dead_letter() re-queues item

**test_circuit_breaker.py:**
- Test starts in CLOSED state
- Test after 5 failures → transitions to OPEN
- Test OPEN state → can_deliver returns False
- Test after recovery timeout → transitions to HALF_OPEN
- Test HALF_OPEN + success → back to CLOSED
- Test HALF_OPEN + failure → back to OPEN
- Test reset() → returns to CLOSED
- Test record_success() resets failure counter

**test_webhook_events.py:**
- Test on_attendance_entry() dispatches correct event type and payload
- Test on_student_created() includes all required fields
- Test on_device_offline() includes device info

**test_webhook_api.py:**
- Test GET /webhooks/stats returns correct structure
- Test POST /webhooks/{id}/test delivers test ping
- Test GET /webhooks/{id}/circuit-breaker returns status
- Test POST /webhooks/{id}/circuit-breaker/reset resets state
- Test GET /webhooks/dead-letter returns list

After completing, verify:
1. All tests pass: pytest tests/test_webhooks/ -v
2. Create a webhook via API pointing to https://webhook.site (for manual testing)
3. Trigger a student creation → verify webhook delivered
4. Verify signature matches on receiving end
5. Test retry by pointing webhook to non-existent URL
6. Verify circuit breaker opens after 5 failures
```

Phase 6

This is Phase 6 of "AttendX" — Face Recognition Attendance Platform. Phases 1-5 are complete (setup, backend core, hikvision worker, REST API, webhook system). Now implement the full Frontend dashboard.

Read the existing frontend directory first — React + TypeScript + Vite + TailwindCSS + shadcn/ui should already be initialized from Phase 1. Build on top of that.

## TASK: Implement Frontend Dashboard (Phase 6)

### 1. Project Configuration & Setup:

**vite.config.ts:**
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  }
})
```

**tsconfig.json paths:**
```json
{
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Initialize shadcn/ui components needed:**
- button, input, label, card, table, dialog, dropdown-menu, select, badge, avatar
- tabs, toast (sonner), skeleton, separator, sheet, popover, calendar, command
- alert, alert-dialog, checkbox, textarea, switch, progress

**src/index.css — Tailwind + shadcn theme:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    /* ... full shadcn theme variables */
  }
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark theme variables */
  }
}
```


### 2. TypeScript Types (src/types/index.ts):

```typescript
// === Auth ===
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  username: string;
  email: string | null;
  role: 'superadmin' | 'admin' | 'teacher';
  is_active: boolean;
  last_login_at: string | null;
}

// === Students ===
export interface Student {
  id: string;
  external_id: string | null;
  employee_no: string;
  name: string;
  class_name: string;
  phone: string | null;
  parent_phone: string | null;
  face_registered: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentCreate {
  name: string;
  class_name: string;
  phone?: string;
  parent_phone?: string;
  external_id?: string;
  employee_no?: string;
}

export interface StudentUpdate extends Partial<StudentCreate> {}

export interface StudentImportResult {
  total: number;
  created: number;
  updated: number;
  errors: Array<{ row: number; message: string }>;
}

// === Attendance ===
export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  class_name: string;
  device_name: string | null;
  event_time: string;
  event_type: 'entry' | 'exit';
  verify_mode: string;
}

export interface AttendanceStats {
  total_students: number;
  present_today: number;
  absent_today: number;
  attendance_percentage: number;
  by_class: Record<string, {
    total: number;
    present: number;
    absent: number;
    percentage: number;
  }>;
}

export interface DailyAttendance {
  date: string;
  present: number;
  absent: number;
  percentage: number;
}

// === Devices ===
export interface Device {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  is_entry: boolean;
  is_active: boolean;
  last_online_at: string | null;
  model: string | null;
  serial_number: string | null;
}

export interface DeviceCreate {
  name: string;
  ip_address: string;
  port?: number;
  username?: string;
  password: string;
  is_entry?: boolean;
}

export interface DeviceHealth {
  id: number;
  name: string;
  is_online: boolean;
  last_online_at: string | null;
  response_time_ms: number | null;
}

// === Webhooks ===
export interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  description: string | null;
  created_at: string;
}

export interface WebhookLog {
  id: string;
  webhook_id: string;
  event_type: string;
  payload: Record<string, any>;
  response_status: number | null;
  attempts: number;
  success: boolean;
  created_at: string;
}

// === API Response ===
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: {
    timestamp: string;
    request_id?: string;
  };
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: { timestamp: string };
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  meta: { timestamp: string };
}
```


### 3. API Service Layer (src/services/api.ts):

```typescript
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor: attach JWT token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 (token refresh), errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });
        
        const { access_token } = response.data.data;
        useAuthStore.getState().setAccessToken(access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

**Create individual API modules:**

**src/services/authApi.ts:**
```typescript
export const authApi = {
  login: (data: LoginRequest) => api.post<ApiResponse<TokenResponse>>('/auth/login', data),
  refresh: (refreshToken: string) => api.post<ApiResponse<TokenResponse>>('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get<ApiResponse<User>>('/auth/me'),
  changePassword: (data: { old_password: string; new_password: string }) => api.post('/auth/change-password', data),
};
```

**src/services/studentsApi.ts:**
```typescript
export const studentsApi = {
  list: (params: { page?: number; per_page?: number; class_name?: string; search?: string; sort?: string }) =>
    api.get<PaginatedResponse<Student>>('/students', { params }),
  get: (id: string) => api.get<ApiResponse<Student>>(`/students/${id}`),
  create: (data: StudentCreate) => api.post<ApiResponse<Student>>('/students', data),
  update: (id: string, data: StudentUpdate) => api.put<ApiResponse<Student>>(`/students/${id}`, data),
  delete: (id: string) => api.delete(`/students/${id}`),
  uploadFace: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<Student>>(`/students/${id}/face`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ApiResponse<StudentImportResult>>('/students/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  export: (params?: { class_name?: string; format?: string }) =>
    api.get('/students/export', { params, responseType: 'blob' }),
};
```

**src/services/attendanceApi.ts:**
```typescript
export const attendanceApi = {
  list: (params: { page?: number; per_page?: number; date_from?: string; date_to?: string; class_name?: string; event_type?: string }) =>
    api.get<PaginatedResponse<AttendanceRecord>>('/attendance', { params }),
  today: (classname?: string) => api.get<ApiResponse<AttendanceRecord[]>>('/attendance/today', { params: { class_name: classname } }),
  stats: (date?: string, className?: string) => api.get<ApiResponse<AttendanceStats>>('/attendance/stats', { params: { date, class_name: className } }),
  weekly: (startDate?: string, className?: string) => api.get<ApiResponse<DailyAttendance[]>>('/attendance/weekly', { params: { start_date: startDate, class_name: className } }),
  report: (params: { date_from: string; date_to: string; class_name?: string; format?: string }) =>
    api.get('/attendance/report', { params, responseType: 'blob' }),
  studentHistory: (studentId: string, params?: { date_from?: string; date_to?: string }) =>
    api.get<ApiResponse<any>>(`/attendance/student/${studentId}`, { params }),
};
```

**src/services/devicesApi.ts:**
```typescript
export const devicesApi = {
  list: () => api.get<ApiResponse<Device[]>>('/devices'),
  create: (data: DeviceCreate) => api.post<ApiResponse<Device>>('/devices', data),
  update: (id: number, data: Partial<DeviceCreate>) => api.put<ApiResponse<Device>>(`/devices/${id}`, data),
  delete: (id: number) => api.delete(`/devices/${id}`),
  sync: (id: number) => api.post(`/devices/${id}/sync`),
  health: (id: number) => api.get<ApiResponse<DeviceHealth>>(`/devices/${id}/health`),
};
```

**src/services/webhooksApi.ts:**
```typescript
export const webhooksApi = {
  list: () => api.get<ApiResponse<Webhook[]>>('/webhooks'),
  create: (data: { url: string; events: string[]; description?: string }) => api.post<ApiResponse<Webhook>>('/webhooks', data),
  update: (id: string, data: Partial<{ url: string; events: string[]; is_active: boolean }>) => api.put<ApiResponse<Webhook>>(`/webhooks/${id}`, data),
  delete: (id: string) => api.delete(`/webhooks/${id}`),
  logs: (id: string, params?: { page?: number; per_page?: number; success?: boolean }) =>
    api.get<PaginatedResponse<WebhookLog>>(`/webhooks/${id}/logs`, { params }),
  test: (id: string) => api.post(`/webhooks/${id}/test`),
  stats: () => api.get<ApiResponse<any>>('/webhooks/stats'),
};
```


### 4. State Management:

**src/store/authStore.ts (Zustand):**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  
  setTokens: (access: string, refresh: string) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setTokens: (access, refresh) => set({
        accessToken: access,
        refreshToken: refresh,
        isAuthenticated: true,
      }),
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user) => set({ user }),
      logout: () => set({
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
      }),
    }),
    {
      name: 'attendx-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
```

**src/store/uiStore.ts:**
```typescript
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    set({ theme });
  },
}));
```


### 5. Router & Layout (src/App.tsx):

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';

// Layouts
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';

// Pages
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Students from '@/pages/Students';
import StudentDetail from '@/pages/StudentDetail';
import Attendance from '@/pages/Attendance';
import Devices from '@/pages/Devices';
import Webhooks from '@/pages/Webhooks';
import Reports from '@/pages/Reports';
import Settings from '@/pages/Settings';
import Users from '@/pages/Users';
import NotFound from '@/pages/NotFound';

// Guards
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { RoleGuard } from '@/components/auth/RoleGuard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,       // 30 seconds
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
          </Route>

          {/* Protected */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/students" element={<Students />} />
              <Route path="/students/:id" element={<StudentDetail />} />
              <Route path="/attendance" element={<Attendance />} />
              <Route path="/reports" element={<Reports />} />
              
              {/* Admin only */}
              <Route element={<RoleGuard roles={['superadmin', 'admin']} />}>
                <Route path="/devices" element={<Devices />} />
                <Route path="/webhooks" element={<Webhooks />} />
                <Route path="/settings" element={<Settings />} />
              </Route>

              {/* Super Admin only */}
              <Route element={<RoleGuard roles={['superadmin']} />}>
                <Route path="/users" element={<Users />} />
              </Route>
            </Route>
          </Route>

          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors closeButton />
    </QueryClientProvider>
  );
}
```


### 6. Layout Components:

**src/components/layout/DashboardLayout.tsx:**
```
Full dashboard layout with:
- Sidebar (collapsible):
  - Logo: "AttendX" with face-scan icon
  - Navigation items with icons (lucide-react):
    - Dashboard (LayoutDashboard)
    - O'quvchilar (Users)
    - Davomat (ClipboardCheck)
    - Hisobotlar (FileBarChart)
    - Qurilmalar (Monitor) — admin only
    - Webhooks (Webhook) — admin only
    - Foydalanuvchilar (UserCog) — superadmin only
    - Sozlamalar (Settings) — admin only
  - Active item highlighted with primary color
  - Collapse button at bottom
  
- Header:
  - Hamburger menu (mobile)
  - Page title (dynamic based on route)
  - Right side: theme toggle (sun/moon), notification bell (badge count), user dropdown:
    - User avatar + name + role badge
    - Dropdown: Profile, Settings, Logout

- Main content area: <Outlet /> with padding
- Footer: "AttendX v1.0.0 • © 2026"
- Responsive: sidebar becomes sheet/drawer on mobile (<768px)
```

**src/components/layout/AuthLayout.tsx:**
```
Centered card layout for login page:
- Full screen with gradient background
- Card in center: logo, form, footer
```

**src/components/auth/ProtectedRoute.tsx:**
```typescript
// Check useAuthStore.isAuthenticated
// If not authenticated → Navigate to /login
// If authenticated → fetch /auth/me to validate token, set user
// Show loading spinner during validation
// Render <Outlet /> when ready
```

**src/components/auth/RoleGuard.tsx:**
```typescript
// Check user.role against allowed roles prop
// If not authorized → Navigate to / with toast "Ruxsat yo'q"
// If authorized → <Outlet />
```


### 7. Dashboard Page (src/pages/Dashboard.tsx):

This is the main page — real-time attendance overview.

```
Layout:
┌─────────────────────────────────────────────────────┐
│  Stat Cards (4 columns, responsive)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Jami     │ │ Keldi ✅ │ │ Kelmadi ❌│ │ Foiz % │ │
│  │ 1,250    │ │ 1,180    │ │ 70       │ │ 94.4%  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                     │
│  ┌──────────────────────┐ ┌─────────────────────┐   │
│  │ Haftalik davomat     │ │ Qurilmalar holati   │   │
│  │ (Bar Chart - recharts│ │ ● Asosiy kirish ✅  │   │
│  │  7 kun, keldi/kelma) │ │ ● Orqa kirish ✅    │   │
│  │                      │ │ ● Sport zal ❌      │   │
│  └──────────────────────┘ └─────────────────────┘   │
│                                                     │
│  ┌──────────────────────┐ ┌─────────────────────┐   │
│  │ Sinf bo'yicha davomat│ │ So'nggi eventlar    │   │
│  │ (Pie/Donut chart)    │ │ (Live feed, last 20)│   │
│  │ 5-A: 95%, 5-B: 88%  │ │ 09:01 Ali ✅ Kirish │   │
│  │ 6-A: 92%             │ │ 09:02 Vali ✅ Kirish│   │
│  └──────────────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Use TanStack Query hooks:**
```typescript
// Auto-refresh every 30 seconds
const { data: stats } = useQuery({
  queryKey: ['attendance', 'stats'],
  queryFn: () => attendanceApi.stats(),
  refetchInterval: 30000,
});

const { data: weekly } = useQuery({
  queryKey: ['attendance', 'weekly'],
  queryFn: () => attendanceApi.weekly(),
});

const { data: devices } = useQuery({
  queryKey: ['devices'],
  queryFn: () => devicesApi.list(),
  refetchInterval: 30000,
});

const { data: todayEvents } = useQuery({
  queryKey: ['attendance', 'today'],
  queryFn: () => attendanceApi.today(),
  refetchInterval: 10000, // refresh every 10 sec
});
```

**Stat Cards component:** Animated number counting, color-coded (green for present, red for absent), arrow up/down vs yesterday.

**Charts:** Use recharts:
- BarChart for weekly (stacked: present green, absent red)
- PieChart/DonutChart for by_class attendance
- Responsive containers


### 8. Students Page (src/pages/Students.tsx):

```
Full CRUD management page:

┌─────────────────────────────────────────────────────┐
│  Header: "O'quvchilar"                              │
│  [+ Yangi o'quvchi] [📥 Import] [📤 Export]        │
│                                                     │
│  Filters bar:                                       │
│  [🔍 Qidiruv...] [Sinf: Barchasi ▼] [Holat ▼]    │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ DataTable                                       ││
│  │ ☐ │ Ism         │ Sinf │ Tel    │ Yuz │ Holat  ││
│  │ ☐ │ Ali Valiyev │ 5-A  │ +998..│ ✅  │ Faol   ││
│  │ ☐ │ Vali Karimov│ 5-B  │ +998..│ ❌  │ Faol   ││
│  │ ☐ │ Olim Toshev │ 6-A  │ +998..│ ✅  │ Nofaol ││
│  │───────────────────────────────────────────────  ││
│  │ ◀ 1 2 3 ... 12 ▶   Ko'rsatilmoqda: 1-20 / 240 ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Features:**
- **DataTable** with sortable columns, row selection, pagination
- **Search** with debounce (300ms) using useDeferredValue or custom hook
- **Class filter** dropdown populated from distinct class names
- **Create dialog:** Form with react-hook-form + zod validation
  - Fields: name*, class_name*, phone, parent_phone, external_id
  - On submit: mutation via useMutation, invalidate query, toast success
- **Edit dialog:** Same form, pre-filled with student data
- **Delete confirmation:** AlertDialog "Rostdan o'chirmoqchimisiz?"
- **Face upload:** Click student row → detail panel/dialog → drag & drop image area
  - Preview uploaded image
  - Show face_registered status badge
- **Import dialog:**
  - Drag & drop Excel file
  - Show progress
  - Show results: created X, updated Y, errors Z
  - Download error report
- **Export button:** Download xlsx directly
- **Bulk actions:** Select multiple → bulk delete (admin only)

**TanStack Query integration:**
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['students', { page, perPage, className, search, sort }],
  queryFn: () => studentsApi.list({ page, per_page: perPage, class_name: className, search, sort }),
  keepPreviousData: true,
});

const createMutation = useMutation({
  mutationFn: studentsApi.create,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['students'] });
    toast.success("O'quvchi qo'shildi");
  },
  onError: (err) => toast.error(err.response?.data?.error?.message || "Xatolik"),
});
```


### 9. Student Detail Page (src/pages/StudentDetail.tsx):

```
Route: /students/:id

┌─────────────────────────────────────────────────────┐
│  ← Orqaga                                          │
│                                                     │
│  ┌──────────┐  Ali Valiyev                         │
│  │  [Face   │  Sinf: 5-A │ Employee: ATX-000001   │
│  │  Image]  │  Tel: +998901234567                   │
│  │          │  Ota-ona: +998901234568               │
│  └──────────┘  Yuz: ✅ Ro'yxatga olingan           │
│                                                     │
│  Tabs:                                              │
│  [Davomat] [Ma'lumotlar] [Yuz boshqaruvi]          │
│                                                     │
│  Davomat tab:                                       │
│  - Date range picker                                │
│  - Attendance history table                         │
│  - Stats: jami X kun, keldi Y, kelmadi Z, foiz W%  │
│  - Mini chart (last 30 days)                        │
│                                                     │
│  Ma'lumotlar tab:                                   │
│  - Edit form (inline or dialog)                     │
│                                                     │
│  Yuz tab:                                           │
│  - Current face image (if registered)               │
│  - Upload new / replace                             │
│  - Sync status per device                           │
└─────────────────────────────────────────────────────┘
```


### 10. Attendance Page (src/pages/Attendance.tsx):

```
┌─────────────────────────────────────────────────────┐
│  Header: "Davomat"                                  │
│                                                     │
│  Filters:                                           │
│  [📅 Sana: Bugun ▼] [Sinf: Barchasi ▼]            │
│  [Turi: Barchasi ▼] [📤 Hisobot yuklash]          │
│                                                     │
│  Stats bar:                                         │
│  Jami: 1250 │ Keldi: 1180 │ Kelmadi: 70 │ 94.4%   │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ DataTable                                       ││
│  │ # │ Ism         │ Sinf │ Vaqt  │ Turi  │ Quril ││
│  │ 1 │ Ali Valiyev │ 5-A  │ 08:45 │ ✅Kir │ Asosiy││
│  │ 2 │ Vali Karimov│ 5-B  │ 08:47 │ ✅Kir │ Asosiy││
│  │ 3 │ Ali Valiyev │ 5-A  │ 14:30 │ 🏠Chiq│ Orqa  ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  Date range picker for historical view              │
│  Calendar heatmap (optional, attendance by day)     │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Date picker (shadcn calendar + popover)
- Real-time: auto-refresh every 10 seconds for today
- Color-coded event types: green for entry, orange for exit
- Export button → download xlsx/pdf
- Click student name → navigate to student detail


### 11. Devices Page (src/pages/Devices.tsx):

```
┌─────────────────────────────────────────────────────┐
│  Header: "Qurilmalar"  [+ Yangi qurilma]           │
│                                                     │
│  Device cards grid (responsive 1-3 columns):        │
│  ┌──────────────────┐ ┌──────────────────┐          │
│  │ 🟢 Asosiy kirish │ │ 🟢 Orqa kirish   │          │
│  │ 192.168.1.100:80 │ │ 192.168.1.101:80 │          │
│  │ DS-K1T341CMF     │ │ DS-K1T671M       │          │
│  │ Ping: 12ms       │ │ Ping: 8ms        │          │
│  │ Oxirgi: 2 sec    │ │ Oxirgi: 5 sec    │          │
│  │ [Sync] [✏️] [🗑️]│ │ [Sync] [✏️] [🗑️]│          │
│  └──────────────────┘ └──────────────────┘          │
│                                                     │
│  ┌──────────────────┐                               │
│  │ 🔴 Sport zal     │                               │
│  │ 192.168.1.102:80 │                               │
│  │ Offline          │                               │
│  │ Oxirgi: 15 min   │                               │
│  │ [Sync] [✏️] [🗑️]│                               │
│  └──────────────────┘                               │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Card-based layout (not table) for devices
- Real-time status indicator (green dot = online, red = offline)
- Health info from Redis via API
- Sync button with loading spinner
- Create/Edit dialog: name, IP, port, username, password, is_entry toggle
- Delete confirmation
- Auto-refresh every 15 seconds


### 12. Webhooks Page (src/pages/Webhooks.tsx):

```
┌─────────────────────────────────────────────────────┐
│  Header: "Webhooks"  [+ Yangi webhook]              │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ DataTable                                       ││
│  │ URL                │ Events │ Holat │ Actions   ││
│  │ https://mbi.uz/... │ 3 ta   │ 🟢   │ [📋][✏️] ││
│  │ https://kundalik...│ 2 ta   │ 🟢   │ [📋][✏️] ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  Webhook detail (expandable or dialog):             │
│  - URL, subscribed events (badges)                  │
│  - Circuit breaker status                           │
│  - Delivery logs table:                             │
│    Time │ Event │ Status │ Attempts │ Duration      │
│  - [Test] [Reset Circuit Breaker] buttons           │
└─────────────────────────────────────────────────────┘
```


### 13. Reports Page (src/pages/Reports.tsx):

```
┌─────────────────────────────────────────────────────┐
│  Header: "Hisobotlar"                               │
│                                                     │
│  Report type cards:                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │ 📊 Kunlik    │ │ 📊 Haftalik  │ │ 📊 Oylik    │ │
│  │ Bugungi      │ │ Shu hafta    │ │ Shu oy      │ │
│  │ davomat      │ │ davomat      │ │ davomat     │ │
│  │ [Yuklash]    │ │ [Yuklash]    │ │ [Yuklash]   │ │
│  └──────────────┘ └──────────────┘ └─────────────┘ │
│                                                     │
│  Custom report builder:                             │
│  [📅 Dan] [📅 Gacha] [Sinf ▼] [Format: XLSX|PDF]  │
│  [📥 Hisobot yaratish]                              │
│                                                     │
│  Recent reports (download history — local state):   │
│  - 2026-02-17 Kunlik 5-A.xlsx [⬇️]                 │
│  - 2026-02-10-16 Haftalik.pdf [⬇️]                 │
└─────────────────────────────────────────────────────┘
```


### 14. Settings Page (src/pages/Settings.tsx):

```
Tabs:
- Umumiy: App name, timezone, default language
- Xavfsizlik: Change password, API keys management
- Bildirishnomalar: Telegram bot status, notification preferences
- Tizim: Database stats, Redis stats, disk usage
```


### 15. Users Page (src/pages/Users.tsx — SuperAdmin only):

```
CRUD for admin/teacher user accounts:
- DataTable: username, email, role, status, last login
- Create: username, email, password, role (admin/teacher)
- Edit: change role, activate/deactivate
- Cannot delete superadmin
```


### 16. Reusable Components (src/components/):

**src/components/common/DataTable.tsx:**
```typescript
// Generic reusable table component
// Props: columns, data, pagination, sorting, onSort, onPageChange, loading, selectable
// Features:
// - Column visibility toggle
// - Sortable column headers (click to sort, arrow indicator)
// - Row selection with checkbox
// - Loading skeleton state
// - Empty state ("Ma'lumot topilmadi" with illustration)
// - Responsive: horizontal scroll on mobile
// Use shadcn/ui Table components internally
```

**src/components/common/StatCard.tsx:**
```typescript
// Props: title, value, icon, trend (up/down/neutral), color, description
// Animated number on change
// Icon from lucide-react
```

**src/components/common/PageHeader.tsx:**
```typescript
// Props: title, description, actions (ReactNode for buttons)
// Consistent page header across all pages
```

**src/components/common/ConfirmDialog.tsx:**
```typescript
// Props: title, description, onConfirm, variant (danger/warning/info)
// Uses AlertDialog from shadcn
```

**src/components/common/FileUpload.tsx:**
```typescript
// Props: accept, maxSize, onUpload, preview
// Drag & drop zone with dashed border
// File type validation
// Size validation
// Preview for images
// Progress indicator
```

**src/components/common/DateRangePicker.tsx:**
```typescript
// Props: from, to, onChange
// Uses shadcn Calendar + Popover
// Preset buttons: Bugun, Shu hafta, Shu oy, Oxirgi 30 kun
```

**src/components/common/EmptyState.tsx:**
```typescript
// Props: icon, title, description, action (button)
// Centered illustration with message
```

**src/components/common/LoadingSkeleton.tsx:**
```typescript
// Table skeleton, card skeleton, chart skeleton variants
```

**src/components/common/StatusBadge.tsx:**
```typescript
// Props: status ('online'|'offline'|'active'|'inactive'|'entry'|'exit')
// Color-coded badge with dot indicator
```


### 17. Custom Hooks (src/hooks/):

**src/hooks/useStudents.ts:**
```typescript
export function useStudents(params) {
  return useQuery({ queryKey: ['students', params], queryFn: ... });
}
export function useCreateStudent() {
  return useMutation({ mutationFn: studentsApi.create, onSuccess: invalidate... });
}
export function useUpdateStudent() { ... }
export function useDeleteStudent() { ... }
export function useImportStudents() { ... }
```

**src/hooks/useAttendance.ts:**
```typescript
export function useAttendanceStats(date?, className?) { ... }
export function useWeeklyAttendance(startDate?, className?) { ... }
export function useTodayAttendance(className?) { ... }
```

**src/hooks/useDevices.ts:**
```typescript
export function useDevices() { ... }
export function useDeviceHealth(id) { ... }
export function useSyncDevice() { return useMutation(...) }
```

**src/hooks/useAuth.ts:**
```typescript
export function useLogin() { return useMutation(...) }
export function useLogout() { ... }
export function useCurrentUser() { return useQuery(...) }
```

**src/hooks/useDebounce.ts:**
```typescript
export function useDebounce<T>(value: T, delay: number = 300): T { ... }
```

**src/hooks/useDownload.ts:**
```typescript
export function useDownload() {
  // Helper to trigger browser file download from blob response
  const download = (blob: Blob, filename: string) => { ... }
  return { download };
}
```


### 18. Theme & Dark Mode:

- ThemeProvider using useUIStore
- Toggle button in header (Sun/Moon icon)
- Persist preference in localStorage
- All components must work in both light and dark mode
- Use Tailwind dark: variants


### 19. Responsive Design:

All pages must be fully responsive:
- Mobile (<640px): Single column, sidebar as drawer, simplified tables
- Tablet (640-1024px): Two columns, collapsible sidebar
- Desktop (>1024px): Full layout with sidebar

Key responsive patterns:
- DataTable → Card list on mobile
- Stat cards → 2x2 grid on tablet, single column on mobile
- Charts → full width on mobile, stacked
- Dialogs → full screen on mobile (sheet from bottom)


### 20. Error & Loading States:

Every page must handle:
- **Loading:** Skeleton placeholders (not spinners)
- **Error:** Error card with retry button, toast for transient errors
- **Empty:** EmptyState component with relevant message and action
- **Offline:** Banner at top "Internet aloqasi yo'q"

Global error boundary:
```typescript
// src/components/ErrorBoundary.tsx
// Catch React errors, show fallback UI with "Xatolik yuz berdi" + reload button
```


After completing, verify:
1. pnpm dev starts without errors on port 3000
2. Login page works → redirects to dashboard
3. Dashboard shows stats (use seed data from backend)
4. All CRUD operations work for Students, Devices, Webhooks
5. Attendance page shows data with filters
6. Reports download works (xlsx)
7. Responsive: test on mobile viewport (Chrome DevTools)
8. Dark mode toggle works
9. Logout works → redirects to login
10. Role-based: teacher cannot see Devices/Webhooks pages
```

Phase 7

This is Phase 7 of "AttendX" — Face Recognition Attendance Platform. Phases 1-6 are complete (setup, backend core, hikvision worker, REST API, webhook system, frontend). Now implement the Telegram Bot fully.

Read the existing codebase first — models (TelegramSub), notification processor, and bot placeholder files exist from previous phases.

## TASK: Implement Telegram Bot (Phase 7)

### 1. Bot Setup & Entry Point (backend/bot/main.py):

```python
"""
AttendX Telegram Bot — Real-time attendance notifications for parents.

Run: python -m bot.main
"""
import asyncio
import signal
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from app.config import get_settings

settings = get_settings()

# Conversation states
PHONE_VERIFY = 0
SELECT_CHILD = 1
SETTINGS_MENU = 2

class AttendXBot:
    def __init__(self):
        self.app: Application | None = None
        self.db_session_factory = None
        self.redis = None

    async def initialize(self) -> None:
        """Initialize database, Redis, and bot application."""
        # 1. Create async database session factory
        # 2. Create Redis client
        # 3. Build telegram Application
        self.app = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .build()
        )
        
        # Store db and redis in bot_data for access in handlers
        self.app.bot_data["db_session_factory"] = self.db_session_factory
        self.app.bot_data["redis"] = self.redis
        
        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all bot command and message handlers."""
        
        # Conversation handler for registration flow
        registration_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start_command)],
            states={
                PHONE_VERIFY: [
                    MessageHandler(filters.CONTACT, phone_received),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, phone_text_received),
                ],
                SELECT_CHILD: [
                    CallbackQueryHandler(child_selected, pattern=r"^child_"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_command)],
            per_user=True,
        )
        
        self.app.add_handler(registration_handler)
        self.app.add_handler(CommandHandler("davomat", davomat_command))
        self.app.add_handler(CommandHandler("hafta", hafta_command))
        self.app.add_handler(CommandHandler("sozlamalar", sozlamalar_command))
        self.app.add_handler(CommandHandler("yordam", yordam_command))
        self.app.add_handler(CommandHandler("status", status_command))
        
        # Callback query handler for settings buttons
        self.app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings_"))
        
        # Unknown command handler
        self.app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    async def start(self) -> None:
        """Start the bot with long polling (development) or webhook (production)."""
        await self.initialize()
        
        if settings.LOG_LEVEL == "DEBUG":
            # Development: Long polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
            
            # Also start notification listener
            await asyncio.gather(
                self._notification_listener(),
                self._keep_alive(),
            )
        else:
            # Production: Webhook mode
            await self.app.run_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path=f"bot/{settings.TELEGRAM_BOT_TOKEN}",
                webhook_url=f"https://{settings.WEBHOOK_DOMAIN}/bot/{settings.TELEGRAM_BOT_TOKEN}",
            )

    async def _notification_listener(self) -> None:
        """Listen to Redis pub/sub for attendance notifications and send to subscribers."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe("notifications:telegram")
        
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await self._send_attendance_notification(data)

    async def _send_attendance_notification(self, data: dict) -> None:
        """Send attendance notification to all subscribed parents."""
        student_id = data["student_id"]
        
        async with self.db_session_factory() as session:
            # Find all active telegram subscriptions for this student
            result = await session.execute(
                select(TelegramSub).where(
                    TelegramSub.student_id == student_id,
                    TelegramSub.is_active == True
                )
            )
            subs = result.scalars().all()
            
            for sub in subs:
                message = format_attendance_message(data)
                try:
                    await self.app.bot.send_message(
                        chat_id=sub.chat_id,
                        text=message,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.error("Failed to send Telegram message",
                               chat_id=sub.chat_id, error=str(e))

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()


def main():
    bot = AttendXBot()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(bot.shutdown()))
    
    try:
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        loop.run_until_complete(bot.shutdown())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
```


### 2. Registration Flow — /start Handler (backend/bot/handlers/start.py):

```python
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /start command — begin registration flow.
    
    Flow:
    1. Greet the user
    2. Check if already registered
    3. If registered → show welcome back message with children list
    4. If not registered → ask for phone number
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        # Check existing subscription
        result = await session.execute(
            select(TelegramSub).where(
                TelegramSub.chat_id == chat_id,
                TelegramSub.is_active == True
            )
        )
        existing = result.scalars().all()
        
        if existing:
            # Already registered
            student_names = []
            for sub in existing:
                student = await session.get(Student, sub.student_id)
                if student:
                    student_names.append(f"👤 {student.name} ({student.class_name})")
            
            names_text = "\n".join(student_names)
            await update.message.reply_text(
                f"👋 Xush kelibsiz!\n\n"
                f"Siz allaqachon ro'yxatdan o'tgansiz.\n"
                f"Farzandlaringiz:\n{names_text}\n\n"
                f"📋 /davomat — Bugungi davomat\n"
                f"📊 /hafta — Haftalik hisobot\n"
                f"⚙️ /sozlamalar — Sozlamalar\n"
                f"❓ /yordam — Yordam",
                parse_mode="HTML",
            )
            return ConversationHandler.END
        
        # Not registered — ask for phone
        keyboard = [
            [KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "👋 <b>AttendX</b> — Davomat Monitoring tizimiga xush kelibsiz!\n\n"
            "Farzandingizning maktabga kelish/ketish xabarlarini olish uchun "
            "telefon raqamingizni tasdiqlang.\n\n"
            "Quyidagi tugmani bosing yoki raqamingizni +998XXXXXXXXX formatda yozing:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return PHONE_VERIFY


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle shared contact (phone number button pressed).
    """
    contact = update.message.contact
    phone = contact.phone_number
    
    # Normalize phone: remove +, spaces, etc.
    phone = normalize_phone(phone)
    
    return await _verify_phone(update, context, phone)


async def phone_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle manually typed phone number.
    """
    phone = update.message.text.strip()
    phone = normalize_phone(phone)
    
    # Validate format
    if not is_valid_phone(phone):
        await update.message.reply_text(
            "❌ Noto'g'ri format. Iltimos +998XXXXXXXXX formatda yozing.\n"
            "Masalan: +998901234567"
        )
        return PHONE_VERIFY
    
    return await _verify_phone(update, context, phone)


async def _verify_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str) -> int:
    """
    Core phone verification logic.
    
    1. Search students table where parent_phone matches
    2. If found:
       a. One child → auto-link and confirm
       b. Multiple children → show selection (inline keyboard)
    3. If not found → error message with admin contact
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        # Search for students with this parent_phone
        # Try multiple phone formats: with/without +, with/without 998
        phone_variants = generate_phone_variants(phone)
        
        result = await session.execute(
            select(Student).where(
                Student.parent_phone.in_(phone_variants),
                Student.is_active == True
            )
        )
        students = result.scalars().all()
        
        if not students:
            await update.message.reply_text(
                "❌ Bu telefon raqam bazada topilmadi.\n\n"
                "Iltimos, maktab administratori bilan bog'laning va "
                "telefon raqamingiz tizimga kiritilganligini tekshiring.\n\n"
                "Qayta urinish uchun /start bosing.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        
        if len(students) == 1:
            # Single child — auto-link
            student = students[0]
            sub = TelegramSub(
                chat_id=chat_id,
                phone=phone,
                student_id=student.id,
                is_active=True,
            )
            session.add(sub)
            await session.commit()
            
            await update.message.reply_text(
                f"✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
                f"👤 <b>{student.name}</b>\n"
                f"📚 Sinf: {student.class_name}\n\n"
                f"Endi farzandingiz maktabga kelganda va ketganda xabar olasiz.\n\n"
                f"📋 /davomat — Bugungi davomat\n"
                f"📊 /hafta — Haftalik hisobot",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML",
            )
            return ConversationHandler.END
        
        else:
            # Multiple children — ask which ones to subscribe
            context.user_data["students"] = {str(s.id): s for s in students}
            context.user_data["phone"] = phone
            
            keyboard = []
            for student in students:
                keyboard.append([InlineKeyboardButton(
                    f"👤 {student.name} ({student.class_name})",
                    callback_data=f"child_{student.id}"
                )])
            keyboard.append([InlineKeyboardButton(
                "✅ Hammasini tanlash",
                callback_data="child_all"
            )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"📱 Telefon raqamingizga {len(students)} ta farzand topildi.\n"
                f"Qaysi biri uchun xabar olmoqchisiz?",
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return SELECT_CHILD


async def child_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle child selection callback."""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    phone = context.user_data.get("phone", "")
    students = context.user_data.get("students", {})
    db_session_factory = context.bot_data["db_session_factory"]
    
    selection = query.data  # "child_{id}" or "child_all"
    
    async with db_session_factory() as session:
        linked = []
        
        if selection == "child_all":
            for student_id, student in students.items():
                sub = TelegramSub(
                    chat_id=chat_id,
                    phone=phone,
                    student_id=student.id,
                    is_active=True,
                )
                session.add(sub)
                linked.append(f"👤 {student.name} ({student.class_name})")
        else:
            student_id = selection.replace("child_", "")
            student = students.get(student_id)
            if student:
                sub = TelegramSub(
                    chat_id=chat_id,
                    phone=phone,
                    student_id=student.id,
                    is_active=True,
                )
                session.add(sub)
                linked.append(f"👤 {student.name} ({student.class_name})")
        
        await session.commit()
        
        names_text = "\n".join(linked)
        await query.edit_message_text(
            f"✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
            f"{names_text}\n\n"
            f"Endi xabar olasiz.\n\n"
            f"📋 /davomat — Bugungi davomat\n"
            f"📊 /hafta — Haftalik hisobot",
            parse_mode="HTML",
        )
    
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration."""
    await update.message.reply_text(
        "❌ Bekor qilindi. Qayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
```


### 3. Phone Utilities (backend/bot/utils.py):

```python
import re

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to consistent format.
    Input variants: +998901234567, 998901234567, 8901234567, 901234567
    Output: 998901234567 (no + prefix)
    """
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Handle various formats
    if len(digits) == 12 and digits.startswith('998'):
        return digits  # Already correct: 998901234567
    elif len(digits) == 9 and digits[0] in '0123456789':
        return f'998{digits}'  # 901234567 → 998901234567
    elif len(digits) == 10 and digits.startswith('8'):
        return f'998{digits[1:]}'  # 8901234567 → 998901234567
    elif len(digits) == 13 and digits.startswith('8998'):
        return digits[1:]  # 8998901234567 → 998901234567
    
    return digits


def generate_phone_variants(phone: str) -> list[str]:
    """
    Generate all possible phone format variants for DB search.
    This handles cases where parent_phone was entered in different formats.
    """
    normalized = normalize_phone(phone)
    
    if len(normalized) == 12 and normalized.startswith('998'):
        short = normalized[3:]  # 901234567
        return [
            normalized,           # 998901234567
            f"+{normalized}",     # +998901234567
            short,                # 901234567
            f"8{short}",          # 8901234567
            f"+998{short}",       # +998901234567
            f"+998 {short[:2]} {short[2:5]} {short[5:]}",  # +998 90 123 4567
        ]
    
    return [phone, normalized]


def is_valid_phone(phone: str) -> bool:
    """Validate Uzbekistan phone number format."""
    normalized = normalize_phone(phone)
    return len(normalized) == 12 and normalized.startswith('998')


def format_time(dt_string: str) -> str:
    """Format datetime string to HH:MM."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%H:%M")
    except:
        return dt_string
```


### 4. Attendance Command (backend/bot/handlers/attendance.py):

```python
async def davomat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /davomat — Show today's attendance for subscribed children.
    
    Output format:
    📋 Bugungi davomat — 2026-02-19
    
    👤 Ali Valiyev (5-A)
    ✅ Kirish: 08:45 — Asosiy kirish
    🏠 Chiqish: 14:30 — Orqa chiqish
    
    👤 Vali Valiyev (3-B)
    ✅ Kirish: 08:52 — Asosiy kirish
    ⏳ Hali chiqmagan
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        # Get all subscriptions for this chat
        subs = await _get_active_subs(session, chat_id)
        
        if not subs:
            await update.message.reply_text(
                "❌ Siz hali ro'yxatdan o'tmagansiz.\n/start bosing."
            )
            return
        
        today = date.today()
        response_parts = [f"📋 <b>Bugungi davomat</b> — {today.strftime('%Y-%m-%d')}\n"]
        
        for sub in subs:
            student = await session.get(Student, sub.student_id)
            if not student:
                continue
            
            # Get today's attendance for this student
            result = await session.execute(
                select(AttendanceLog)
                .where(
                    AttendanceLog.student_id == student.id,
                    func.date(AttendanceLog.event_time) == today
                )
                .order_by(AttendanceLog.event_time.asc())
            )
            records = result.scalars().all()
            
            part = f"\n👤 <b>{student.name}</b> ({student.class_name})\n"
            
            if not records:
                part += "❌ Bugun kelmagan\n"
            else:
                for record in records:
                    time_str = record.event_time.strftime("%H:%M")
                    if record.event_type == "entry":
                        part += f"✅ Kirish: {time_str}"
                    else:
                        part += f"🏠 Chiqish: {time_str}"
                    
                    # Add device name if available
                    if record.device_id:
                        device = await session.get(Device, record.device_id)
                        if device:
                            part += f" — {device.name}"
                    part += "\n"
                
                # Check if still at school (last event is entry)
                last_event = records[-1]
                if last_event.event_type == "entry":
                    part += "⏳ Hali chiqmagan\n"
            
            response_parts.append(part)
        
        await update.message.reply_text(
            "\n".join(response_parts),
            parse_mode="HTML",
        )
```


### 5. Weekly Report Command (backend/bot/handlers/attendance.py):

```python
async def hafta_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /hafta — Show weekly attendance report.
    
    Output format:
    📊 Haftalik hisobot — 13.02 – 19.02.2026
    
    👤 Ali Valiyev (5-A)
    Du  13.02  ✅ Keldi (08:45)
    Se  14.02  ✅ Keldi (08:40)
    Ch  15.02  ❌ Kelmadi
    Pa  16.02  ✅ Keldi (08:50)
    Ju  17.02  ✅ Keldi (08:42)
    Sh  18.02  — Dam olish
    Ya  19.02  ✅ Keldi (08:38)
    
    📈 Davomat: 5/6 kun (83.3%)
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        subs = await _get_active_subs(session, chat_id)
        
        if not subs:
            await update.message.reply_text("❌ Siz hali ro'yxatdan o'tmagansiz.\n/start bosing.")
            return
        
        # Calculate week range (Monday to Sunday)
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        day_names_uz = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
        
        response_parts = [
            f"📊 <b>Haftalik hisobot</b> — {monday.strftime('%d.%m')} – {sunday.strftime('%d.%m.%Y')}\n"
        ]
        
        for sub in subs:
            student = await session.get(Student, sub.student_id)
            if not student:
                continue
            
            # Get all attendance for this week
            result = await session.execute(
                select(AttendanceLog)
                .where(
                    AttendanceLog.student_id == student.id,
                    func.date(AttendanceLog.event_time) >= monday,
                    func.date(AttendanceLog.event_time) <= sunday,
                    AttendanceLog.event_type == "entry"  # Count entries only
                )
                .order_by(AttendanceLog.event_time.asc())
            )
            entries = result.scalars().all()
            
            # Build day-by-day map
            entry_dates = {}
            for entry in entries:
                d = entry.event_time.date()
                if d not in entry_dates:
                    entry_dates[d] = entry.event_time.strftime("%H:%M")
            
            part = f"\n👤 <b>{student.name}</b> ({student.class_name})\n"
            present_days = 0
            school_days = 0
            
            for i in range(7):
                day = monday + timedelta(days=i)
                day_name = day_names_uz[i]
                day_str = day.strftime("%d.%m")
                
                if i >= 5:  # Saturday, Sunday
                    part += f"{day_name}  {day_str}  — Dam olish\n"
                elif day > today:
                    part += f"{day_name}  {day_str}  ⏳ Hali kelmagan\n"
                else:
                    school_days += 1
                    if day in entry_dates:
                        present_days += 1
                        part += f"{day_name}  {day_str}  ✅ Keldi ({entry_dates[day]})\n"
                    else:
                        part += f"{day_name}  {day_str}  ❌ Kelmadi\n"
            
            percentage = (present_days / school_days * 100) if school_days > 0 else 0
            part += f"\n📈 Davomat: {present_days}/{school_days} kun ({percentage:.1f}%)\n"
            
            response_parts.append(part)
        
        await update.message.reply_text(
            "\n".join(response_parts),
            parse_mode="HTML",
        )
```


### 6. Settings Command (backend/bot/handlers/settings.py):

```python
async def sozlamalar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /sozlamalar — Show settings menu with inline keyboard.
    """
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        subs = await _get_active_subs(session, chat_id)
        
        if not subs:
            await update.message.reply_text("❌ Siz hali ro'yxatdan o'tmagansiz.\n/start bosing.")
            return
        
        # Build settings keyboard
        keyboard = [
            [InlineKeyboardButton(
                "🔔 Xabarlarni o'chirish" if sub.is_active else "🔕 Xabarlarni yoqish",
                callback_data=f"settings_toggle_{sub.student_id}"
            )]
            for sub in subs
        ]
        keyboard.append([InlineKeyboardButton("🗑 Ro'yxatdan chiqish", callback_data="settings_unsubscribe")])
        keyboard.append([InlineKeyboardButton("📱 Farzand qo'shish", callback_data="settings_add_child")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Build current status text
        status_lines = []
        for sub in subs:
            student = await session.get(Student, sub.student_id)
            if student:
                icon = "🔔" if sub.is_active else "🔕"
                status_lines.append(f"{icon} {student.name} ({student.class_name})")
        
        await update.message.reply_text(
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"Xabar olish holati:\n" + "\n".join(status_lines),
            reply_markup=reply_markup,
            parse_mode="HTML",
        )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    action = query.data  # settings_toggle_{id}, settings_unsubscribe, settings_add_child
    db_session_factory = context.bot_data["db_session_factory"]
    
    async with db_session_factory() as session:
        if action.startswith("settings_toggle_"):
            student_id = action.replace("settings_toggle_", "")
            result = await session.execute(
                select(TelegramSub).where(
                    TelegramSub.chat_id == chat_id,
                    TelegramSub.student_id == student_id
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.is_active = not sub.is_active
                await session.commit()
                status = "yoqildi 🔔" if sub.is_active else "o'chirildi 🔕"
                await query.edit_message_text(f"✅ Xabarlar {status}\n\n/sozlamalar — qayta ko'rish")
        
        elif action == "settings_unsubscribe":
            # Deactivate all subscriptions
            result = await session.execute(
                select(TelegramSub).where(TelegramSub.chat_id == chat_id)
            )
            subs = result.scalars().all()
            for sub in subs:
                sub.is_active = False
            await session.commit()
            await query.edit_message_text(
                "✅ Ro'yxatdan chiqdingiz.\nQayta ro'yxatdan o'tish: /start"
            )
        
        elif action == "settings_add_child":
            await query.edit_message_text(
                "Yangi farzand qo'shish uchun /start bosing va telefon raqamingizni kiriting."
            )
```


### 7. Help & Status Commands (backend/bot/handlers/common.py):

```python
async def yordam_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yordam — Show help message."""
    await update.message.reply_text(
        "❓ <b>AttendX Bot — Yordam</b>\n\n"
        "📋 /davomat — Bugungi davomat holati\n"
        "📊 /hafta — Haftalik davomat hisoboti\n"
        "⚙️ /sozlamalar — Xabar olish sozlamalari\n"
        "📱 /start — Qayta ro'yxatdan o'tish\n"
        "ℹ️ /status — Bot holati\n"
        "❓ /yordam — Shu yordam xabari\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "Farzandingiz maktabga kelganda yoki ketganda "
        "avtomatik xabar olasiz.\n\n"
        "<b>Muammo bo'lsa:</b>\n"
        "Maktab administratori bilan bog'laning.",
        parse_mode="HTML",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — Show bot and system status."""
    chat_id = update.effective_chat.id
    db_session_factory = context.bot_data["db_session_factory"]
    redis = context.bot_data["redis"]
    
    async with db_session_factory() as session:
        subs = await _get_active_subs(session, chat_id)
        
        # Get device count from Redis
        online_count = 0
        total_devices = await session.execute(select(func.count(Device.id)).where(Device.is_active == True))
        total = total_devices.scalar()
        
        # Check online devices from Redis
        for i in range(1, total + 1):
            status = await redis.get(f"device:{i}:online")
            if status == b"1":
                online_count += 1
        
        await update.message.reply_text(
            f"ℹ️ <b>AttendX Bot Status</b>\n\n"
            f"🤖 Bot: ✅ Ishlayapti\n"
            f"📡 Terminallar: {online_count}/{total} online\n"
            f"👤 Sizning obunalar: {len(subs)} ta\n"
            f"🕐 Server vaqti: {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML",
        )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Noma'lum buyruq.\n/yordam — barcha buyruqlar ro'yxati"
    )
```


### 8. Notification Message Templates (backend/bot/templates.py):

```python
def format_attendance_message(data: dict) -> str:
    """
    Format attendance notification for Telegram.
    
    Entry: ✅ Ali Valiyev maktabga keldi
    Exit:  🏠 Ali Valiyev maktabdan ketdi
    """
    event_type = data.get("event_type", "entry")
    student_name = data.get("student_name", "Noma'lum")
    class_name = data.get("class_name", "")
    event_time = data.get("event_time", "")
    device_name = data.get("device_name", "")
    
    # Format time
    try:
        dt = datetime.fromisoformat(event_time)
        time_str = dt.strftime("%H:%M")
    except:
        time_str = event_time
    
    if event_type == "entry":
        return (
            f"✅ <b>{student_name}</b> maktabga keldi\n"
            f"📚 {class_name}\n"
            f"🕐 {time_str}\n"
            f"📍 {device_name}"
        )
    else:
        return (
            f"🏠 <b>{student_name}</b> maktabdan ketdi\n"
            f"📚 {class_name}\n"
            f"🕐 {time_str}\n"
            f"📍 {device_name}"
        )


def format_late_notification(data: dict, threshold_time: str = "08:30") -> str:
    """Format late arrival notification."""
    return (
        f"⚠️ <b>{data['student_name']}</b> kechikib keldi\n"
        f"📚 {data['class_name']}\n"
        f"🕐 {data.get('arrival_time', '')} (belgilangan: {threshold_time})\n"
        f"📍 {data.get('device_name', '')}"
    )


def format_absent_notification(student_name: str, class_name: str, date_str: str) -> str:
    """Format absence notification (sent at end of school day)."""
    return (
        f"❌ <b>{student_name}</b> bugun maktabga kelmadi\n"
        f"📚 {class_name}\n"
        f"📅 {date_str}"
    )


def format_weekly_summary(student_name: str, class_name: str, present: int, total: int) -> str:
    """Format weekly summary notification (sent on Friday/Saturday)."""
    percentage = (present / total * 100) if total > 0 else 0
    bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
    
    return (
        f"📊 <b>Haftalik hisobot</b>\n\n"
        f"👤 {student_name} ({class_name})\n"
        f"📈 {bar} {percentage:.0f}%\n"
        f"✅ Keldi: {present} kun\n"
        f"❌ Kelmadi: {total - present} kun\n"
        f"📅 Jami: {total} ish kuni"
    )
```


### 9. Keyboard Layouts (backend/bot/keyboards.py):

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

def phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with phone number share button."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Davomat", callback_data="menu_davomat")],
        [InlineKeyboardButton("📊 Haftalik", callback_data="menu_hafta")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="menu_sozlamalar")],
    ])

def children_keyboard(students: list) -> InlineKeyboardMarkup:
    """Keyboard for selecting children."""
    keyboard = [
        [InlineKeyboardButton(
            f"👤 {s.name} ({s.class_name})",
            callback_data=f"child_{s.id}"
        )]
        for s in students
    ]
    keyboard.append([InlineKeyboardButton("✅ Hammasini tanlash", callback_data="child_all")])
    return InlineKeyboardMarkup(keyboard)
```


### 10. Helper Functions (backend/bot/helpers.py):

```python
async def _get_active_subs(session: AsyncSession, chat_id: int) -> list[TelegramSub]:
    """Get all active Telegram subscriptions for a chat."""
    result = await session.execute(
        select(TelegramSub).where(
            TelegramSub.chat_id == chat_id,
            TelegramSub.is_active == True
        )
    )
    return result.scalars().all()


async def get_subscriber_count(session: AsyncSession) -> int:
    """Get total active subscriber count."""
    result = await session.execute(
        select(func.count(TelegramSub.id)).where(TelegramSub.is_active == True)
    )
    return result.scalar() or 0


async def send_to_student_subscribers(
    bot: Bot,
    db_session_factory,
    student_id: str,
    message: str,
    parse_mode: str = "HTML"
) -> dict:
    """
    Send a message to all subscribers of a student.
    Returns: {sent: int, failed: int, errors: list}
    """
    sent = 0
    failed = 0
    errors = []
    
    async with db_session_factory() as session:
        subs = await session.execute(
            select(TelegramSub).where(
                TelegramSub.student_id == student_id,
                TelegramSub.is_active == True
            )
        )
        
        for sub in subs.scalars().all():
            try:
                await bot.send_message(
                    chat_id=sub.chat_id,
                    text=message,
                    parse_mode=parse_mode,
                )
                sent += 1
                # Rate limiting: Telegram allows 30 messages/second
                await asyncio.sleep(0.05)  # 50ms between messages
            except Exception as e:
                failed += 1
                errors.append({"chat_id": sub.chat_id, "error": str(e)})
    
    return {"sent": sent, "failed": failed, "errors": errors}
```


### 11. Update Worker Notification Processor:

Update `backend/worker/notifications/processor.py` to publish to "notifications:telegram" channel (in addition to existing webhook notifications):

```python
# In _handle_attendance_notification method, add:
await self.redis.publish("notifications:telegram", json.dumps({
    "student_id": str(data["student_id"]),
    "student_name": data["student_name"],
    "class_name": data["class_name"],
    "event_type": data["event_type"],
    "event_time": data["event_time"],
    "device_name": data.get("device_name", ""),
}))
```


### 12. Docker Integration:

Add bot service to docker-compose.yml:
```yaml
bot:
  build:
    context: ./backend
    dockerfile: Dockerfile
  command: python -m bot.main
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - LOG_LEVEL=${LOG_LEVEL}
  depends_on:
    - db
    - redis
  networks:
    - attendx-network
  restart: unless-stopped
```


### 13. Bot Admin Notifications (backend/bot/admin_alerts.py):

Send critical alerts to a Telegram admin channel/group:

```python
class AdminAlerter:
    """Send critical system alerts to admin Telegram channel."""
    
    def __init__(self, bot: Bot, admin_chat_id: int):
        self.bot = bot
        self.admin_chat_id = admin_chat_id
    
    async def device_offline_alert(self, device_name: str, ip: str) -> None:
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"🔴 <b>Terminal oflayn!</b>\n\n"
                 f"📡 {device_name}\n"
                 f"🌐 {ip}\n"
                 f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML",
        )
    
    async def device_online_alert(self, device_name: str, ip: str) -> None:
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"🟢 <b>Terminal onlayn!</b>\n\n"
                 f"📡 {device_name}\n"
                 f"🌐 {ip}\n"
                 f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML",
        )
    
    async def error_alert(self, error_type: str, details: str) -> None:
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"⚠️ <b>Xatolik!</b>\n\n"
                 f"Turi: {error_type}\n"
                 f"Tafsilot: {details[:500]}\n"
                 f"🕐 {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="HTML",
        )
    
    async def daily_summary(self, stats: dict) -> None:
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"📊 <b>Kunlik hisobot</b>\n\n"
                 f"👥 Jami: {stats['total']}\n"
                 f"✅ Keldi: {stats['present']}\n"
                 f"❌ Kelmadi: {stats['absent']}\n"
                 f"📈 Foiz: {stats['percentage']:.1f}%\n"
                 f"📡 Terminallar: {stats['devices_online']}/{stats['devices_total']}",
            parse_mode="HTML",
        )
```

Add ADMIN_CHAT_ID to .env and config.py:
```
ADMIN_CHAT_ID=0  # Telegram chat/group ID for admin alerts
```


### 14. Tests (backend/tests/test_bot/):

**test_utils.py:**
- Test normalize_phone("998901234567") → "998901234567"
- Test normalize_phone("+998901234567") → "998901234567"
- Test normalize_phone("901234567") → "998901234567"
- Test normalize_phone("8901234567") → "998901234567"
- Test generate_phone_variants() returns all formats
- Test is_valid_phone() with valid/invalid numbers

**test_templates.py:**
- Test format_attendance_message() for entry → contains "maktabga keldi"
- Test format_attendance_message() for exit → contains "maktabdan ketdi"
- Test format_late_notification() contains "kechikib keldi"
- Test format_absent_notification() contains "kelmadi"
- Test format_weekly_summary() contains progress bar and percentage

**test_handlers.py (with mocked bot):**
- Test /start for new user → asks for phone
- Test /start for existing user → shows children list
- Test phone verification with valid phone → links student
- Test phone verification with unknown phone → error message
- Test multiple children → shows selection keyboard
- Test /davomat → shows today's attendance
- Test /hafta → shows weekly report
- Test /sozlamalar → shows settings menu

After completing, verify:
1. Set TELEGRAM_BOT_TOKEN in .env (get from @BotFather)
2. Run: python -m bot.main
3. Open bot in Telegram → /start → share phone → should link
4. /davomat → should show today's attendance
5. /hafta → should show weekly report
6. When student scanned on terminal → notification should arrive in Telegram
7. All tests pass: pytest tests/test_bot/ -v
```

Phase 8

This is Phase 8 of "AttendX" — Face Recognition Attendance Platform. Phases 1-7 are complete. Now implement Security Hardening and Monitoring to make the platform production-ready.

Read the existing codebase first — auth, middleware, exceptions, and logging already exist from previous phases. This phase focuses on hardening security, adding comprehensive monitoring, audit trails, and backup systems.

## TASK: Implement Security & Monitoring (Phase 8)

### 1. Input Validation & Sanitization (app/core/validation.py):

```python
import re
import bleach
from pydantic import validator

class InputSanitizer:
    """Sanitize and validate all user inputs to prevent injection attacks."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """Remove HTML tags, limit length, strip whitespace."""
        if not value:
            return value
        # Strip HTML tags
        cleaned = bleach.clean(value, tags=[], strip=True)
        # Remove null bytes
        cleaned = cleaned.replace('\x00', '')
        # Limit length
        cleaned = cleaned[:max_length].strip()
        return cleaned

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IPv4 address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        parts = ip.split('.')
        return all(0 <= int(p) <= 255 for p in parts)

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number (Uzbekistan format)."""
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 9 and len(digits) <= 13

    @staticmethod
    def validate_employee_no(emp_no: str) -> bool:
        """Validate employee number format."""
        return bool(re.match(r'^[A-Za-z0-9\-_]{1,50}$', emp_no))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize uploaded filename."""
        # Remove path separators and dangerous chars
        cleaned = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove double dots (path traversal)
        cleaned = cleaned.replace('..', '_')
        return cleaned[:200]

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate webhook URL."""
        pattern = r'^https?://[a-zA-Z0-9\-\.]+(:[0-9]+)?(/.*)?$'
        return bool(re.match(pattern, url))
```

Apply sanitization to ALL Pydantic schemas — add validators:
```python
# In schemas/student.py
class StudentCreate(BaseModel):
    name: str
    class_name: str
    
    @validator('name')
    def sanitize_name(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=200)
    
    @validator('class_name')
    def sanitize_class(cls, v):
        return InputSanitizer.sanitize_string(v, max_length=50)
```

Apply similar validators to ALL create/update schemas: StudentCreate, StudentUpdate, DeviceCreate, DeviceUpdate, WebhookCreate, WebhookUpdate, LoginRequest.


### 2. Security Headers Middleware (app/core/security_headers.py):

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (similar to Helmet.js)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Strict Transport Security (HTTPS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        )
        
        # Remove server header
        response.headers.pop("server", None)
        
        return response
```

Register in main.py:
```python
app.add_middleware(SecurityHeadersMiddleware)
```


### 3. CSRF Protection (app/core/csrf.py):

```python
import secrets
from starlette.middleware.base import BaseHTTPMiddleware

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection for state-changing requests.
    
    For API endpoints (JWT/API Key auth) — CSRF not needed (token-based).
    For cookie-based sessions (if any) — require X-CSRF-Token header.
    """
    
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip CSRF for API endpoints (they use Bearer token)
        if request.url.path.startswith("/api/"):
            return await call_next(request)
        
        # For non-API routes, check CSRF token on unsafe methods
        if request.method not in self.SAFE_METHODS:
            csrf_token = request.headers.get("X-CSRF-Token")
            session_token = request.cookies.get("csrf_token")
            
            if not csrf_token or not session_token or csrf_token != session_token:
                return JSONResponse(
                    status_code=403,
                    content={"success": False, "error": {"code": "CSRF_FAILED", "message": "CSRF token mismatch"}}
                )
        
        response = await call_next(request)
        
        # Set CSRF cookie if not present
        if "csrf_token" not in request.cookies:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                "csrf_token", token,
                httponly=False,  # JS needs to read it
                samesite="strict",
                secure=True,
                max_age=3600
            )
        
        return response
```


### 4. Brute Force Protection Enhancement (app/core/rate_limiter.py):

```python
class BruteForceProtection:
    """
    Enhanced brute force protection for login and sensitive endpoints.
    Uses Redis for distributed rate limiting.
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_login_attempt(self, identifier: str) -> dict:
        """
        Check if login attempt is allowed.
        
        Args:
            identifier: username or IP address
            
        Returns:
            {"allowed": bool, "remaining_attempts": int, "locked_until": str | None}
        
        Rules:
        - 5 failed attempts → lock for 15 minutes
        - 10 failed attempts → lock for 1 hour
        - 20 failed attempts → lock for 24 hours
        """
        key = f"bruteforce:login:{identifier}"
        
        attempts = await self.redis.get(key)
        attempts = int(attempts) if attempts else 0
        
        if attempts >= 20:
            ttl = await self.redis.ttl(key)
            return {"allowed": False, "remaining_attempts": 0, "locked_until": f"{ttl}s", "lockout_level": "critical"}
        elif attempts >= 10:
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                return {"allowed": False, "remaining_attempts": 0, "locked_until": f"{ttl}s", "lockout_level": "high"}
        elif attempts >= 5:
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                return {"allowed": False, "remaining_attempts": 0, "locked_until": f"{ttl}s", "lockout_level": "medium"}
        
        remaining = 5 - attempts if attempts < 5 else 0
        return {"allowed": True, "remaining_attempts": max(remaining, 0), "locked_until": None}

    async def record_failed_attempt(self, identifier: str) -> None:
        """Record a failed login attempt."""
        key = f"bruteforce:login:{identifier}"
        attempts = await self.redis.incr(key)
        
        # Set TTL based on attempt count
        if attempts >= 20:
            await self.redis.expire(key, 86400)     # 24 hours
        elif attempts >= 10:
            await self.redis.expire(key, 3600)       # 1 hour
        elif attempts >= 5:
            await self.redis.expire(key, 900)        # 15 minutes
        else:
            await self.redis.expire(key, 900)        # Reset counter after 15 min of inactivity

    async def record_successful_login(self, identifier: str) -> None:
        """Reset failed attempts on successful login."""
        key = f"bruteforce:login:{identifier}"
        await self.redis.delete(key)

    async def check_api_rate_limit(self, api_key: str, max_per_minute: int = 100) -> dict:
        """Rate limit per API key."""
        key = f"ratelimit:api:{api_key}"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 60)
        
        remaining = max(max_per_minute - current, 0)
        return {
            "allowed": current <= max_per_minute,
            "remaining": remaining,
            "reset_in": await self.redis.ttl(key),
        }

    async def get_blocked_ips(self) -> list[dict]:
        """Get all currently blocked IPs/usernames (for admin dashboard)."""
        keys = await self.redis.keys("bruteforce:login:*")
        blocked = []
        for key in keys:
            attempts = await self.redis.get(key)
            ttl = await self.redis.ttl(key)
            identifier = key.decode().replace("bruteforce:login:", "")
            if int(attempts) >= 5:
                blocked.append({
                    "identifier": identifier,
                    "attempts": int(attempts),
                    "locked_for_seconds": ttl,
                })
        return blocked
```

Integrate into auth login endpoint:
```python
# In app/api/v1/auth.py login()
brute_force = BruteForceProtection(redis)

# Check by username
check = await brute_force.check_login_attempt(data.username)
if not check["allowed"]:
    raise AuthenticationException(f"Account locked. Try again in {check['locked_until']}", code="ACCOUNT_LOCKED")

# Check by IP
ip = request.client.host
ip_check = await brute_force.check_login_attempt(f"ip:{ip}")
if not ip_check["allowed"]:
    raise AuthenticationException("Too many attempts from this IP", code="IP_LOCKED")

# On failed login:
await brute_force.record_failed_attempt(data.username)
await brute_force.record_failed_attempt(f"ip:{ip}")

# On successful login:
await brute_force.record_successful_login(data.username)
await brute_force.record_successful_login(f"ip:{ip}")
```


### 5. API Key Rotation (app/core/api_key_manager.py):

```python
class APIKeyManager:
    """Manage API key lifecycle: creation, rotation, revocation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(self, name: str, permissions: list[str] | None = None) -> dict:
        """
        Create new API key.
        Returns: {"key": "atx_xxxx...", "key_id": UUID, "name": str}
        Note: raw key is shown ONLY on creation, never stored.
        """
        raw_key = f"atx_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            permissions=permissions or ["read"],
            is_active=True,
        )
        self.session.add(api_key)
        await self.session.commit()
        
        return {
            "key": raw_key,  # Show only once!
            "key_id": str(api_key.id),
            "name": name,
            "permissions": permissions or ["read"],
        }

    async def rotate_key(self, key_id: str) -> dict:
        """
        Rotate API key: deactivate old, create new with same name/permissions.
        Returns new key details.
        """
        old_key = await self.session.get(APIKey, key_id)
        if not old_key:
            raise NotFoundException("API key not found")
        
        # Deactivate old key
        old_key.is_active = False
        
        # Create new key with same settings
        result = await self.create_key(
            name=f"{old_key.name} (rotated)",
            permissions=old_key.permissions,
        )
        
        await self.session.commit()
        return result

    async def revoke_key(self, key_id: str) -> None:
        """Permanently deactivate an API key."""
        api_key = await self.session.get(APIKey, key_id)
        if api_key:
            api_key.is_active = False
            await self.session.commit()

    async def list_keys(self) -> list[dict]:
        """List all API keys (without raw key values)."""
        result = await self.session.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        keys = result.scalars().all()
        return [
            {
                "id": str(k.id),
                "name": k.name,
                "permissions": k.permissions,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat(),
                "key_preview": "atx_****" + k.key_hash[:8],
            }
            for k in keys
        ]

    @staticmethod
    def verify_key(raw_key: str, key_hash: str) -> bool:
        """Verify a raw API key against stored hash."""
        return hashlib.sha256(raw_key.encode()).hexdigest() == key_hash
```

Add API Key management endpoints:
```python
# app/api/v1/api_keys.py
POST   /api/v1/api-keys          # Create new key (superadmin only)
GET    /api/v1/api-keys          # List all keys
POST   /api/v1/api-keys/{id}/rotate  # Rotate key
DELETE /api/v1/api-keys/{id}     # Revoke key
```


### 6. Comprehensive Audit Log (app/services/audit_service.py):

```python
class AuditService:
    """Track all important actions for compliance and debugging."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        user_id: str | None,
        action: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        self.session.add(entry)
        # Don't commit here — let the caller manage the transaction
        return entry

    async def get_logs(
        self,
        user_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filters."""
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        count_query = select(func.count(AuditLog.id))
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
            count_query = count_query.where(AuditLog.entity_type == entity_type)
        if date_from:
            query = query.where(func.date(AuditLog.created_at) >= date_from)
            count_query = count_query.where(func.date(AuditLog.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(AuditLog.created_at) <= date_to)
            count_query = count_query.where(func.date(AuditLog.created_at) <= date_to)
        
        total = (await self.session.execute(count_query)).scalar()
        results = (await self.session.execute(query.offset(skip).limit(limit))).scalars().all()
        
        return results, total

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete audit logs older than X days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await self.session.commit()
        return result.rowcount
```

**Audit all critical actions** — add audit logging to:
- Login success/failure
- Logout
- Password change
- Student CRUD
- Device CRUD
- Webhook CRUD
- API key operations
- User management
- Settings changes
- Face registration
- Excel import/export

Add audit log API endpoint:
```python
# app/api/v1/audit.py
GET /api/v1/audit-logs    # List with filters (superadmin only)
```


### 7. Sensitive Data Masking (app/core/data_masking.py):

```python
class DataMasker:
    """Mask sensitive data in logs, responses, and audit trails."""

    SENSITIVE_FIELDS = {
        'password', 'password_hash', 'password_enc', 'secret',
        'token', 'access_token', 'refresh_token', 'api_key',
        'fernet_key', 'jwt_secret', 'authorization',
    }

    @classmethod
    def mask_dict(cls, data: dict, depth: int = 0) -> dict:
        """Recursively mask sensitive fields in a dictionary."""
        if depth > 10:
            return data
        
        masked = {}
        for key, value in data.items():
            if key.lower() in cls.SENSITIVE_FIELDS:
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = value[:2] + "***" + value[-2:]
                else:
                    masked[key] = "***"
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value, depth + 1)
            elif isinstance(value, list):
                masked[key] = [
                    cls.mask_dict(item, depth + 1) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked

    @classmethod
    def mask_phone(cls, phone: str) -> str:
        """Mask phone number: +998 90 *** ** 67"""
        if not phone or len(phone) < 6:
            return "***"
        return phone[:6] + "***" + phone[-2:]

    @classmethod
    def mask_email(cls, email: str) -> str:
        """Mask email: a***@gmail.com"""
        if not email or '@' not in email:
            return "***"
        local, domain = email.split('@', 1)
        return local[0] + "***@" + domain
```

Integrate into logging middleware — mask sensitive fields before logging request/response bodies.


### 8. Sentry Integration (app/core/sentry_config.py):

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

def init_sentry(dsn: str | None, environment: str = "production") -> None:
    """Initialize Sentry error tracking."""
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,
        send_default_pii=False,  # Don't send personal data
        
        # Filter sensitive data
        before_send=_filter_sensitive_data,
        before_send_transaction=_filter_transaction,
    )

def _filter_sensitive_data(event, hint):
    """Remove sensitive data from Sentry events."""
    if "request" in event and "data" in event["request"]:
        event["request"]["data"] = DataMasker.mask_dict(event["request"]["data"])
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        for sensitive in ["authorization", "x-api-key", "cookie"]:
            if sensitive in headers:
                headers[sensitive] = "***"
    return event

def _filter_transaction(event, hint):
    """Filter health check transactions."""
    if event.get("transaction") == "/health":
        return None  # Don't track health checks
    return event
```

Add to main.py lifespan:
```python
init_sentry(settings.SENTRY_DSN, environment="production" if settings.LOG_LEVEL != "DEBUG" else "development")
```


### 9. Health Check Endpoints Enhancement (app/api/v1/health.py):

```python
@router.get("/health")
async def basic_health():
    """Basic health check — for uptime monitoring."""
    return {"status": "ok", "version": settings.APP_VERSION, "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health(
    current_user: User = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
):
    """
    Detailed health check — for admin monitoring.
    Checks: database, redis, disk, worker, bot.
    """
    checks = {}
    overall = "ok"
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "type": "postgresql"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)[:100]}
        overall = "degraded"
    
    # Redis check
    try:
        await redis.ping()
        info = await redis.info("memory")
        checks["redis"] = {
            "status": "ok",
            "used_memory": info.get("used_memory_human", "unknown"),
        }
    except Exception as e:
        checks["redis"] = {"status": "error", "message": str(e)[:100]}
        overall = "degraded"
    
    # Disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)
        checks["disk"] = {
            "status": "ok" if free_gb > 1 else "warning",
            "free_gb": round(free_gb, 2),
            "used_percent": round(used / total * 100, 1),
        }
        if free_gb < 1:
            overall = "warning"
    except:
        checks["disk"] = {"status": "unknown"}
    
    # Worker status (check Redis key set by worker)
    worker_heartbeat = await redis.get("worker:heartbeat")
    if worker_heartbeat:
        last_beat = float(worker_heartbeat)
        age = time.time() - last_beat
        checks["worker"] = {
            "status": "ok" if age < 30 else "warning",
            "last_heartbeat_seconds_ago": round(age),
        }
        if age > 60:
            overall = "degraded"
    else:
        checks["worker"] = {"status": "not_running"}
        overall = "degraded"
    
    # Device summary
    online_count = 0
    total_devices_result = await db.execute(
        select(func.count(Device.id)).where(Device.is_active == True)
    )
    total_devices = total_devices_result.scalar() or 0
    
    for i in range(1, total_devices + 50):
        status = await redis.get(f"device:{i}:online")
        if status == b"1":
            online_count += 1
    
    checks["devices"] = {
        "total": total_devices,
        "online": online_count,
    }
    
    # Student and attendance summary
    student_count = (await db.execute(
        select(func.count(Student.id)).where(Student.is_active == True)
    )).scalar() or 0
    
    today_events = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            func.date(AttendanceLog.event_time) == date.today()
        )
    )).scalar() or 0
    
    checks["data"] = {
        "active_students": student_count,
        "today_events": today_events,
    }
    
    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": round(time.time() - APP_START_TIME),
        "checks": checks,
    }
```

Add `APP_START_TIME = time.time()` in main.py at module level.

Add worker heartbeat — in worker/main.py polling loop:
```python
await self.redis.set("worker:heartbeat", str(time.time()))
```


### 10. Prometheus Metrics (app/core/metrics.py) — Optional:

```python
"""
Optional Prometheus metrics.
Install: pip install prometheus-fastapi-instrumentator
"""
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

# Custom metrics
ATTENDANCE_EVENTS = Counter(
    "attendx_attendance_events_total",
    "Total attendance events processed",
    ["event_type", "device_id"]
)

LOGIN_ATTEMPTS = Counter(
    "attendx_login_attempts_total",
    "Total login attempts",
    ["status"]  # success, failed, locked
)

WEBHOOK_DELIVERIES = Counter(
    "attendx_webhook_deliveries_total",
    "Total webhook deliveries",
    ["status", "event_type"]
)

DEVICES_ONLINE = Gauge(
    "attendx_devices_online",
    "Number of online devices"
)

ACTIVE_STUDENTS = Gauge(
    "attendx_active_students",
    "Number of active students"
)

API_REQUEST_DURATION = Histogram(
    "attendx_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint", "status_code"]
)

def setup_metrics(app):
    """Setup Prometheus metrics instrumentation."""
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")
```

Add `prometheus-fastapi-instrumentator` to pyproject.toml.
Call `setup_metrics(app)` in main.py (conditionally, if ENABLE_METRICS=true).


### 11. Backup System (backend/scripts/backup.py):

```python
"""
AttendX Database Backup Script.

Run manually: python -m scripts.backup
Run via cron: 0 2 * * * cd /path/to/attendx/backend && python -m scripts.backup

Features:
- PostgreSQL pg_dump
- Face images backup
- Configuration backup
- Retention policy (keep last 30 days)
- Compression (gzip)
- Optional upload to S3/remote
"""
import subprocess
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta

class BackupManager:
    def __init__(self, backup_dir: str = "/data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_database(self) -> Path:
        """Backup PostgreSQL database using pg_dump."""
        filename = self.backup_dir / f"db_{self.timestamp}.sql.gz"
        
        # pg_dump and gzip
        dump_cmd = [
            "pg_dump",
            "--host", settings.DB_HOST,
            "--port", str(settings.DB_PORT),
            "--username", settings.DB_USER,
            "--dbname", settings.DB_NAME,
            "--no-password",
            "--format", "plain",
        ]
        
        with gzip.open(filename, 'wb') as f:
            process = subprocess.Popen(
                dump_cmd,
                stdout=subprocess.PIPE,
                env={**os.environ, "PGPASSWORD": settings.DB_PASSWORD},
            )
            for chunk in iter(lambda: process.stdout.read(8192), b''):
                f.write(chunk)
            process.wait()
        
        if process.returncode != 0:
            raise Exception(f"pg_dump failed with code {process.returncode}")
        
        size_mb = filename.stat().st_size / (1024 * 1024)
        logger.info(f"Database backup created: {filename} ({size_mb:.1f} MB)")
        return filename

    def backup_face_images(self) -> Path | None:
        """Backup face images directory."""
        faces_dir = Path("/data/faces")
        if not faces_dir.exists():
            return None
        
        filename = self.backup_dir / f"faces_{self.timestamp}.tar.gz"
        shutil.make_archive(
            str(filename).replace('.tar.gz', ''),
            'gztar',
            str(faces_dir.parent),
            faces_dir.name,
        )
        
        logger.info(f"Face images backup created: {filename}")
        return filename

    def backup_config(self) -> Path:
        """Backup .env and configuration files."""
        filename = self.backup_dir / f"config_{self.timestamp}.tar.gz"
        
        config_files = [
            ".env",
            "docker/docker-compose.yml",
            "docker/docker-compose.prod.yml",
            "docker/nginx.conf",
        ]
        
        with tarfile.open(filename, "w:gz") as tar:
            for cf in config_files:
                path = Path(cf)
                if path.exists():
                    tar.add(str(path), arcname=path.name)
        
        logger.info(f"Config backup created: {filename}")
        return filename

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """Delete backups older than retention period."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        
        for file in self.backup_dir.glob("*.gz"):
            if file.stat().st_mtime < cutoff.timestamp():
                file.unlink()
                deleted += 1
        
        logger.info(f"Cleaned up {deleted} old backup files")
        return deleted

    def run_full_backup(self) -> dict:
        """Run complete backup."""
        results = {}
        
        try:
            results["database"] = str(self.backup_database())
        except Exception as e:
            results["database_error"] = str(e)
        
        try:
            face_backup = self.backup_face_images()
            results["faces"] = str(face_backup) if face_backup else "no_faces"
        except Exception as e:
            results["faces_error"] = str(e)
        
        try:
            results["config"] = str(self.backup_config())
        except Exception as e:
            results["config_error"] = str(e)
        
        results["cleanup"] = self.cleanup_old_backups()
        results["timestamp"] = self.timestamp
        
        return results


def main():
    manager = BackupManager()
    results = manager.run_full_backup()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
```

Add backup restore script too:
```python
# backend/scripts/restore.py
# python -m scripts.restore --file /data/backups/db_20260219.sql.gz
```


### 12. Log Aggregation Enhancement (app/core/logging.py):

Update structlog configuration for production-ready JSON logging:

```python
import structlog
import logging
from app.core.data_masking import DataMasker

def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with JSON output."""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            _mask_sensitive_processor,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def _mask_sensitive_processor(logger, method_name, event_dict):
    """Automatically mask sensitive fields in log entries."""
    return DataMasker.mask_dict(event_dict)

def get_logger(name: str = None):
    """Get a structured logger instance."""
    return structlog.get_logger(name)
```


### 13. Security Admin Dashboard API (app/api/v1/security.py):

```python
# Superadmin only endpoints for security monitoring

GET /api/v1/security/blocked-ips        # List currently blocked IPs/users
POST /api/v1/security/unblock/{id}      # Manually unblock an IP/user
GET /api/v1/security/api-keys           # List API keys with usage stats
GET /api/v1/security/audit-logs         # Audit log viewer with filters
GET /api/v1/security/sessions           # Active sessions (tokens in Redis)
POST /api/v1/security/revoke-all-sessions  # Revoke all active tokens
GET /api/v1/security/backup-status      # Last backup info
POST /api/v1/security/backup-now        # Trigger manual backup
```


### 14. Environment Hardening Checklist (docs/security-checklist.md):

Create documentation:
```markdown
# AttendX Production Security Checklist

## Before Deployment
- [ ] Change all default passwords (admin, database, Redis)
- [ ] Generate strong SECRET_KEY (64 chars random)
- [ ] Generate strong JWT_SECRET (32 chars random)
- [ ] Generate Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
- [ ] Set LOG_LEVEL=INFO (not DEBUG)
- [ ] Set ALLOWED_ORIGINS to actual domain only
- [ ] Enable HTTPS (SSL certificate via Let's Encrypt)

## Firewall (ufw)
- [ ] ufw default deny incoming
- [ ] ufw allow 80/tcp (HTTP → redirect to HTTPS)
- [ ] ufw allow 443/tcp (HTTPS)
- [ ] ufw allow 22/tcp (SSH — restrict to admin IP)
- [ ] ufw deny 5432 (PostgreSQL — internal only)
- [ ] ufw deny 6379 (Redis — internal only)
- [ ] ufw enable

## Database
- [ ] PostgreSQL: sslmode=require
- [ ] Change default postgres password
- [ ] Create dedicated DB user (not superuser)
- [ ] Enable pg_hba.conf restrictions

## Monitoring
- [ ] Sentry DSN configured
- [ ] Backup cron job running (daily 2 AM)
- [ ] Health check monitoring (uptime robot or similar)
- [ ] Admin Telegram alerts configured

## Regular Maintenance
- [ ] Rotate API keys every 90 days
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly
- [ ] Test backup restore quarterly
```


### 15. Update main.py — Register All Security Middleware:

```python
# In main.py, add in order:
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Initialize Sentry
init_sentry(settings.SENTRY_DSN)

# Setup metrics (optional)
if settings.ENABLE_METRICS:
    setup_metrics(app)
```


### 16. Dependencies (add to pyproject.toml):
- bleach (input sanitization)
- sentry-sdk[fastapi] (error tracking)
- prometheus-fastapi-instrumentator (optional, metrics)


### 17. Tests (backend/tests/test_security/):

**test_validation.py:**
- Test sanitize_string removes HTML tags
- Test sanitize_string handles null bytes
- Test validate_ip_address with valid/invalid IPs
- Test validate_phone with various formats
- Test sanitize_filename removes path traversal
- Test validate_url with valid/invalid URLs

**test_brute_force.py:**
- Test 5 failed attempts → locked for 15 min
- Test 10 failed attempts → locked for 1 hour
- Test successful login → resets counter
- Test IP-based rate limiting

**test_api_key_manager.py:**
- Test create_key returns raw key only once
- Test rotate_key deactivates old, creates new
- Test revoke_key deactivates
- Test verify_key with correct/incorrect keys

**test_data_masking.py:**
- Test mask_dict masks password fields
- Test mask_phone shows partial number
- Test mask_email shows partial email
- Test nested dict masking

**test_audit.py:**
- Test audit log creation
- Test audit log filtering by user, action, date
- Test cleanup_old_logs

**test_security_headers.py:**
- Test all security headers present in response
- Test X-Content-Type-Options = nosniff
- Test X-Frame-Options = DENY
- Test CSP header present

After completing, verify:
1. All tests pass: pytest tests/test_security/ -v
2. Security headers visible: curl -I http://localhost:8000/health
3. Brute force: try 6 wrong logins → account locked
4. Audit logs: perform actions → check /api/v1/audit-logs
5. Health check: GET /health/detailed shows all component statuses
6. Backup: python -m scripts.backup → creates backup files
```

Phase 9

This is Phase 9 (FINAL) of "AttendX" — Face Recognition Attendance Platform. Phases 1-8 are complete. Now implement comprehensive testing, Docker production setup, deployment configuration, and documentation.

Read the entire existing codebase first to understand all components before writing tests and deployment configs.

## TASK: Test & Deploy (Phase 9)

=============================================
PART A: COMPREHENSIVE TESTING
=============================================

### 1. Test Configuration (backend/tests/conftest.py):

"""
Central test configuration with fixtures for all test modules.
Uses SQLite async for fast testing (no PostgreSQL required for unit tests).
"""
import asyncio
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, date, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.models.user import User
from app.models.student import Student
from app.models.device import Device
from app.models.attendance import AttendanceLog
from app.models.webhook import Webhook
from app.models.api_key import APIKey
from app.core.dependencies import get_db, get_redis
from app.core.security import hash_password, create_access_token, encrypt_device_password

# Test database (SQLite async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Get a test database session."""
    async with TestSessionLocal() as session:
        yield session


# --- Mock Redis ---
class FakeRedis:
    """In-memory Redis mock for testing."""
    def __init__(self):
        self._store = {}
        self._expiry = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ex=None):
        self._store[key] = value if isinstance(value, bytes) else str(value).encode()
        if ex:
            self._expiry[key] = ex

    async def delete(self, *keys):
        for key in keys:
            self._store.pop(key, None)

    async def incr(self, key):
        val = int(self._store.get(key, b"0"))
        val += 1
        self._store[key] = str(val).encode()
        return val

    async def expire(self, key, seconds):
        self._expiry[key] = seconds

    async def ttl(self, key):
        return self._expiry.get(key, -1)

    async def keys(self, pattern="*"):
        import fnmatch
        return [k.encode() if isinstance(k, str) else k for k in self._store if fnmatch.fnmatch(k, pattern)]

    async def ping(self):
        return True

    async def info(self, section=None):
        return {"used_memory_human": "1M"}

    async def publish(self, channel, message):
        pass

    def pubsub(self):
        return FakePubSub()

    async def zadd(self, key, mapping):
        if key not in self._store:
            self._store[key] = {}
        self._store[key].update(mapping)

    async def zrangebyscore(self, key, min_score, max_score, start=0, num=50):
        return []

    async def zrem(self, key, member):
        return 1

    async def zcard(self, key):
        return len(self._store.get(key, {}))

    async def lpush(self, key, value):
        if key not in self._store:
            self._store[key] = []
        self._store[key].insert(0, value)

    async def llen(self, key):
        return len(self._store.get(key, []))

    async def ltrim(self, key, start, stop):
        pass

    async def lindex(self, key, index):
        lst = self._store.get(key, [])
        return lst[index] if index < len(lst) else None

    async def lrem(self, key, count, value):
        pass


class FakePubSub:
    async def subscribe(self, *channels):
        pass
    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        return None


@pytest_asyncio.fixture
async def fake_redis():
    return FakeRedis()


# --- Override dependencies ---
@pytest_asyncio.fixture
async def client(db_session, fake_redis) -> AsyncClient:
    """Create test HTTP client with dependency overrides."""
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Sample Data Fixtures ---
@pytest_asyncio.fixture
async def admin_user(db_session) -> User:
    """Create test admin user."""
    user = User(
        id=uuid4(),
        username="testadmin",
        email="admin@test.com",
        password_hash=hash_password("TestPass123"),
        role="superadmin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def teacher_user(db_session) -> User:
    """Create test teacher user."""
    user = User(
        id=uuid4(),
        username="testteacher",
        email="teacher@test.com",
        password_hash=hash_password("TestPass123"),
        role="teacher",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(admin_user) -> dict:
    """Get JWT auth headers for admin user."""
    token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def teacher_headers(teacher_user) -> dict:
    """Get JWT auth headers for teacher user."""
    token = create_access_token({"sub": str(teacher_user.id), "role": teacher_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_students(db_session) -> list[Student]:
    """Create 10 sample students."""
    students = []
    classes = ["5-A", "5-B", "6-A"]
    for i in range(10):
        s = Student(
            id=uuid4(),
            name=f"Test Student {i+1}",
            employee_no=f"ATX-{i+1:06d}",
            class_name=classes[i % 3],
            parent_phone=f"99890{i:07d}",
            face_registered=i < 7,
            is_active=True,
        )
        db_session.add(s)
        students.append(s)
    await db_session.commit()
    for s in students:
        await db_session.refresh(s)
    return students


@pytest_asyncio.fixture
async def sample_device(db_session) -> Device:
    """Create a sample device."""
    device = Device(
        name="Test Terminal",
        ip_address="192.168.30.188",
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


@pytest_asyncio.fixture
async def sample_attendance(db_session, sample_students, sample_device) -> list[AttendanceLog]:
    """Create sample attendance records for today."""
    records = []
    today = datetime.now().replace(hour=8, minute=30, second=0)

    for i, student in enumerate(sample_students[:7]):
        entry = AttendanceLog(
            id=uuid4(),
            student_id=student.id,
            device_id=sample_device.id,
            event_time=today + timedelta(minutes=i * 2),
            event_type="entry",
            verify_mode="face",
            raw_event_id=f"evt-entry-{i}",
            notified=True,
        )
        db_session.add(entry)
        records.append(entry)

    await db_session.commit()
    return records


@pytest_asyncio.fixture
async def sample_webhook(db_session) -> Webhook:
    """Create a sample webhook."""
    webhook = Webhook(
        id=uuid4(),
        url="https://example.com/webhook",
        secret="test-secret-key-12345",
        events=["attendance.entry", "attendance.exit", "student.created"],
        is_active=True,
        description="Test webhook",
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


### 2. Auth API Tests (backend/tests/test_api/test_auth.py):

Test cases to implement:
- test_login_success: POST /auth/login with valid creds → 200, returns access + refresh tokens
- test_login_invalid_password: wrong password → 401, INVALID_CREDENTIALS
- test_login_inactive_user: is_active=False → 401
- test_login_nonexistent_user: unknown username → 401
- test_login_brute_force_lockout: 6 failed attempts → 401, ACCOUNT_LOCKED
- test_refresh_token: POST /auth/refresh with valid refresh → 200, new access token
- test_refresh_expired_token: expired refresh → 401
- test_refresh_invalid_token: random string → 401
- test_get_me: GET /auth/me with valid token → 200, user data
- test_get_me_no_token: no Authorization header → 401
- test_get_me_invalid_token: malformed token → 401
- test_logout: POST /auth/logout → 200, then use same token → 401 (blacklisted)
- test_change_password: valid old + new → 200
- test_change_password_wrong_old: wrong old password → 401
- test_change_password_weak: short new password → 422


### 3. Students API Tests (backend/tests/test_api/test_students.py):

Test cases to implement:
- test_list_students: GET /students → 200, paginated response
- test_list_students_pagination: page=2, per_page=3 → correct slice
- test_list_students_filter_class: ?class_name=5-A → only 5-A students
- test_list_students_search: ?search=Student 1 → matching results
- test_list_students_sort: ?sort=-name → descending order
- test_create_student: POST /students with valid data → 201, student created
- test_create_student_auto_employee_no: no employee_no → auto-generated ATX-XXXXXX
- test_create_student_duplicate_external_id: duplicate → 409
- test_create_student_duplicate_employee_no: duplicate → 409
- test_create_student_validation: missing name → 422
- test_get_student: GET /students/{id} → 200
- test_get_student_not_found: non-existent id → 404
- test_update_student: PUT with partial data → 200, only changed fields updated
- test_update_student_not_found: → 404
- test_delete_student: DELETE → 200, student.is_active=False (soft delete)
- test_delete_student_not_found: → 404
- test_create_student_teacher_forbidden: teacher role → 403
- test_list_students_teacher_allowed: teacher can list → 200
- test_export_students: GET /students/export → 200, content-type xlsx
- test_import_students: POST /students/import with xlsx → 200, import results


### 4. Attendance API Tests (backend/tests/test_api/test_attendance.py):

Test cases to implement:
- test_list_attendance: GET /attendance → 200, paginated
- test_list_attendance_date_filter: ?date_from=2026-02-19 → filtered
- test_list_attendance_class_filter: ?class_name=5-A → only 5-A
- test_today_attendance: GET /attendance/today → 200, today's records
- test_attendance_stats: GET /attendance/stats → 200, correct totals (7 present, 3 absent out of 10)
- test_attendance_stats_by_class: → correct per-class breakdown
- test_weekly_stats: GET /attendance/weekly → 200, 7 daily entries
- test_student_attendance: GET /attendance/student/{id} → 200, history + stats
- test_attendance_report_xlsx: GET /attendance/report?format=xlsx → 200, xlsx blob
- test_attendance_teacher_access: teacher can view → 200


### 5. Devices API Tests (backend/tests/test_api/test_devices.py):

Test cases to implement:
- test_list_devices: GET /devices → 200
- test_create_device: POST with valid data → 201, password encrypted
- test_create_device_duplicate_ip: same IP → 409
- test_update_device: PUT → 200
- test_update_device_password: new password → re-encrypted
- test_delete_device: DELETE → 200
- test_device_health: GET /devices/{id}/health → 200
- test_sync_device: POST /devices/{id}/sync → 200, "queued"
- test_devices_teacher_forbidden: teacher → 403
- test_device_not_found: → 404


### 6. Webhooks API Tests (backend/tests/test_api/test_webhooks.py):

Test cases to implement:
- test_list_webhooks: → 200
- test_create_webhook: → 201, secret auto-generated
- test_create_webhook_invalid_url: bad url → 422
- test_create_webhook_invalid_event: unknown event → 422
- test_update_webhook: → 200
- test_delete_webhook: → 200
- test_webhook_logs: GET /webhooks/{id}/logs → 200, paginated
- test_webhook_test_ping: POST /webhooks/{id}/test → 200 (mock target)
- test_webhook_stats: GET /webhooks/stats → 200
- test_webhook_teacher_forbidden: → 403


### 7. Webhook Engine Tests (backend/tests/test_webhooks/test_engine.py):

Test cases to implement:
- test_generate_signature: correct HMAC-SHA256
- test_verify_signature: valid → True, invalid → False
- test_deliver_success: mock httpx 200 → success=True
- test_deliver_timeout: mock timeout → success=False, error="Timeout"
- test_deliver_connection_error: mock error → success=False
- test_deliver_headers: correct X-AttendX-* headers sent
- test_dispatch_event: finds subscribed webhooks and delivers
- test_dispatch_no_subscribers: no webhooks for event → 0 delivered
- test_circuit_breaker_opens: 5 failures → skips delivery
- test_circuit_breaker_recovery: after timeout → half-open → success → closed
- test_retry_queue: failed delivery → queued with correct delay
- test_retry_max_exceeded: 3 retries → dead letter queue


### 8. Hikvision Worker Tests (backend/tests/test_worker/):

test_hikvision_client.py:
- test_get_device_info: mock XML response → parsed correctly
- test_add_user: correct XML body sent
- test_delete_user: correct XML body
- test_register_face: multipart upload with correct parts
- test_get_events: parse event XML, handle pagination
- test_get_events_empty: no events → empty list
- test_check_online_success: 200 response → True
- test_check_online_timeout: timeout → False
- test_retry_on_connection_error: retries 3 times
- test_digest_auth: httpx.DigestAuth used

test_xml_helpers.py:
- test_parse_device_info_xml: extract model, serial, firmware
- test_parse_events_xml: extract all event fields
- test_parse_users_xml: extract employeeNo, name
- test_build_user_xml: correct XML structure
- test_handle_namespace: Hikvision XML namespace handled
- test_parse_error_response: extract error code and message

test_event_poller.py:
- test_process_event_creates_attendance: new event → attendance_log created
- test_process_event_dedup: duplicate raw_event_id → skipped
- test_process_event_publishes_notification: → Redis publish called
- test_poll_device_pagination: handles multi-page events
- test_entry_exit_detection: is_entry device → "entry" type

test_health_checker.py:
- test_device_online: → last_online_at updated
- test_device_offline_alert: was online → now offline → notification published
- test_device_online_alert: was offline → now online → notification published


### 9. Security Tests (backend/tests/test_security/):

test_validation.py:
- test_sanitize_string_removes_html
- test_sanitize_string_removes_null_bytes
- test_sanitize_string_limits_length
- test_validate_ip_valid
- test_validate_ip_invalid
- test_validate_phone_valid_formats
- test_validate_phone_invalid
- test_sanitize_filename_removes_path_traversal
- test_validate_url_valid
- test_validate_url_invalid

test_security_headers.py:
- test_x_content_type_options_present
- test_x_frame_options_deny
- test_csp_header_present
- test_hsts_header_present
- test_referrer_policy_present

test_brute_force.py:
- test_5_failures_locks_15min
- test_10_failures_locks_1hour
- test_success_resets_counter
- test_ip_rate_limiting

test_data_masking.py:
- test_mask_password_field
- test_mask_token_field
- test_mask_nested_dict
- test_mask_phone
- test_mask_email

test_encryption.py:
- test_fernet_encrypt_decrypt: encrypt → decrypt → original
- test_password_hash_verify: hash → verify → True
- test_password_wrong: hash → verify wrong → False
- test_jwt_create_verify: create → decode → correct payload
- test_jwt_expired: expired token → exception


### 10. Bot Tests (backend/tests/test_bot/):

test_utils.py:
- test_normalize_phone_with_plus
- test_normalize_phone_without_plus
- test_normalize_phone_short
- test_normalize_phone_with_8
- test_generate_phone_variants_count
- test_is_valid_phone_valid
- test_is_valid_phone_invalid

test_templates.py:
- test_format_entry_message
- test_format_exit_message
- test_format_late_notification
- test_format_absent_notification
- test_format_weekly_summary_with_bar


### 11. Integration Tests (backend/tests/test_integration/):

test_full_flow.py — End-to-end flow tests:

async def test_complete_attendance_flow(client, auth_headers, db_session):
    """
    Full integration test:
    1. Create student via API
    2. Create device via API
    3. Simulate attendance event (record via service)
    4. Query attendance via API → student appears
    5. Get stats → correct numbers
    6. Export report → valid xlsx
    """

async def test_student_lifecycle(client, auth_headers):
    """
    1. Create student
    2. Update student
    3. Upload face image
    4. List students → found
    5. Delete student → soft deleted
    6. List students → not in active list
    """

async def test_webhook_delivery_flow(client, auth_headers, db_session):
    """
    1. Create webhook subscription
    2. Create student → webhook triggered with student.created
    3. Check webhook logs → delivery recorded
    """

async def test_auth_full_flow(client, admin_user):
    """
    1. Login → get tokens
    2. Access protected endpoint → success
    3. Refresh token → new access token
    4. Logout → token blacklisted
    5. Use old token → rejected
    """

async def test_role_based_access(client, auth_headers, teacher_headers):
    """
    1. Admin creates student → 201
    2. Teacher tries to create → 403
    3. Teacher lists students → 200
    4. Admin accesses devices → 200
    5. Teacher accesses devices → 403
    """


### 12. Load Test Configuration (backend/tests/load/locustfile.py):

"""
Load testing with Locust.
Run: locust -f tests/load/locustfile.py --host http://localhost:8000
Target: 500+ concurrent users
"""
from locust import HttpUser, task, between

class AttendXUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def get_dashboard_stats(self):
        self.client.get("/api/v1/attendance/stats", headers=self.headers())

    @task(3)
    def get_today_attendance(self):
        self.client.get("/api/v1/attendance/today", headers=self.headers())

    @task(3)
    def list_students(self):
        self.client.get("/api/v1/students?page=1&per_page=20", headers=self.headers())

    @task(2)
    def get_weekly_stats(self):
        self.client.get("/api/v1/attendance/weekly", headers=self.headers())

    @task(1)
    def list_devices(self):
        self.client.get("/api/v1/devices", headers=self.headers())

    @task(1)
    def health_check(self):
        self.client.get("/health")


=============================================
PART B: DOCKER & PRODUCTION DEPLOYMENT
=============================================

### 13. Production Dockerfile (backend/Dockerfile):

# ===== Stage 1: Builder =====
FROM python:3.11-slim as builder
WORKDIR /build
RUN pip install --no-cache-dir poetry==1.7.1
COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --without-hashes --no-dev > requirements.txt

# ===== Stage 2: Runtime =====
FROM python:3.11-slim as runtime

# Security: non-root user
RUN groupadd -r attendx && useradd -r -g attendx attendx
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /data/faces /data/backups /data/logs \
    && chown -R attendx:attendx /data

# Switch to non-root user
USER attendx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]


### 14. Frontend Dockerfile (frontend/Dockerfile):

# ===== Stage 1: Build =====
FROM node:18-alpine as builder
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# ===== Stage 2: Serve =====
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

Frontend nginx.conf (frontend/nginx.conf):
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}


### 15. Production Docker Compose (docker/docker-compose.prod.yml):

version: "3.8"

services:
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: attendx-backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - FERNET_KEY=${FERNET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - SENTRY_DSN=${SENTRY_DSN}
      - LOG_LEVEL=INFO
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    volumes:
      - face_data:/data/faces
      - backup_data:/data/backups
      - logs:/data/logs
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - attendx-network
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G

  worker:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: attendx-worker
    command: python -m worker.main
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - FERNET_KEY=${FERNET_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - face_data:/data/faces
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - attendx-network
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G

  bot:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: attendx-bot
    command: python -m bot.main
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - LOG_LEVEL=INFO
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - attendx-network
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: attendx-frontend
    restart: unless-stopped
    networks:
      - attendx-network

  db:
    image: postgres:15-alpine
    container_name: attendx-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-attendx}
      POSTGRES_USER: ${POSTGRES_USER:-attendx}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-attendx}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - attendx-network
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: attendx-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - attendx-network

  nginx:
    image: nginx:alpine
    container_name: attendx-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot
    depends_on:
      - backend
      - frontend
    networks:
      - attendx-network

volumes:
  postgres_data:
  redis_data:
  face_data:
  backup_data:
  logs:
  certbot_data:

networks:
  attendx-network:
    driver: bridge


### 16. Production Nginx Config (docker/nginx.conf):

worker_processes auto;
events { worker_connections 1024; }

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '$request_time';
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 10M;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;

    upstream backend {
        server backend:8000;
    }
    upstream frontend {
        server frontend:80;
    }

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name _;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL (uncomment when certificates are ready)
        # ssl_certificate /etc/nginx/ssl/fullchain.pem;
        # ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        # ssl_protocols TLSv1.2 TLSv1.3;
        # ssl_ciphers HIGH:!aNULL:!MD5;
        # ssl_prefer_server_ciphers on;

        # For development without SSL:
        listen 80;

        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 60s;
        }

        # Login (stricter rate limit)
        location /api/v1/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Health check (no rate limit)
        location /health {
            proxy_pass http://backend;
        }

        # API docs
        location ~ ^/(docs|redoc|openapi.json) {
            proxy_pass http://backend;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
        }

        # Static files cache
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            proxy_pass http://frontend;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }
}


### 17. SSL Certificate Setup Script (docker/setup-ssl.sh):

#!/bin/bash
DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: ./setup-ssl.sh <domain> <email>"
    exit 1
fi

docker run -it --rm \
    -v $(pwd)/ssl:/etc/letsencrypt \
    -v $(pwd)/certbot_data:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d $DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email

echo "SSL certificate created for $DOMAIN"
echo "Update nginx.conf to uncomment SSL settings"


### 18. Systemd Services (for non-Docker deployment):

Create docs/systemd/ directory with service files:

attendx-backend.service:
[Unit]
Description=AttendX Backend API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=attendx
Group=attendx
WorkingDirectory=/opt/attendx/backend
Environment=PATH=/opt/attendx/backend/.venv/bin:/usr/bin
EnvironmentFile=/opt/attendx/.env
ExecStart=/opt/attendx/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

attendx-worker.service:
[Unit]
Description=AttendX Hikvision Worker
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=attendx
Group=attendx
WorkingDirectory=/opt/attendx/backend
Environment=PATH=/opt/attendx/backend/.venv/bin:/usr/bin
EnvironmentFile=/opt/attendx/.env
ExecStart=/opt/attendx/backend/.venv/bin/python -m worker.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

attendx-bot.service:
[Unit]
Description=AttendX Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=attendx
Group=attendx
WorkingDirectory=/opt/attendx/backend
Environment=PATH=/opt/attendx/backend/.venv/bin:/usr/bin
EnvironmentFile=/opt/attendx/.env
ExecStart=/opt/attendx/backend/.venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Backup timer (attendx-backup.timer):
[Unit]
Description=AttendX Daily Backup Timer

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target


=============================================
PART C: DOCUMENTATION
=============================================

### 19. README.md (project root):

Create a comprehensive README.md with:
- Project title and description
- Features list
- Quick Start (Docker) — 5 commands
- Quick Start (Manual) — backend, worker, bot, frontend
- Architecture diagram (ASCII):
  Frontend → Backend API → PostgreSQL
                ↕               ↕
             Redis        Hikvision Terminals
                ↕
         Telegram Bot / Worker
- API Documentation links (/docs, /redoc)
- Environment Variables reference
- Testing commands
- Deployment link
- License: MIT


### 20. Installation Guide (docs/installation-guide.md):

Step-by-step production deployment guide:
1. Server tayyorlash (Ubuntu, Docker, firewall)
2. AttendX o'rnatish (git clone)
3. .env faylni to'ldirish (SECRET_KEY, JWT_SECRET, FERNET_KEY generation commands)
4. Ishga tushirish (docker-compose.prod.yml)
5. SSL sertifikat (Let's Encrypt)
6. Backup cron sozlash
7. Terminal qo'shish


### 21. Admin User Guide (docs/admin-guide.md):

Administrator guide with sections:
1. Dashboard — statistika, grafiklar
2. O'quvchilar boshqaruvi — CRUD, import, face upload
3. Qurilmalar — terminal qo'shish, sync
4. Davomat — ko'rish, filter, export
5. Webhooks — tashqi tizim integratsiya
6. Telegram Bot — sozlash


### 22. Troubleshooting Guide (docs/troubleshooting.md):

Common issues and fixes:
- Terminal Offline — IP, port, password, ISAPI, Worker
- Login ishlamayapti — creds, locked, backend, database
- Yuz tanilmayapti — rasm sifati, format, sync
- Telegram xabar kelmayapti — token, bot, phone, Redis
- Webhook ishlamayapti — URL, active, circuit breaker
- Database xatolik — PostgreSQL, migration, disk
- Server sekin — CPU, RAM, Redis, logs


### 23. API Reference (docs/api-reference.md):

Complete API reference:
- Auth: login, refresh, logout, me
- Students: CRUD, import, export, face upload
- Attendance: list, today, stats, weekly, report
- Devices: CRUD, sync, health
- Webhooks: CRUD, logs, test
- Error codes table


### 24. Postman Collection (docs/attendx-api.postman_collection.json):

Create Postman collection with:
- All endpoints organized by folder
- Pre-request script for auto Bearer token
- Environment variables
- Example request/response
- Test scripts


### 25. Final Verification Script (backend/scripts/verify_deployment.py):

"""
Post-deployment verification script.
Usage: python -m scripts.verify_deployment
"""
import asyncio
import httpx

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def main():
    async with httpx.AsyncClient(timeout=10) as client:
        print("🔍 AttendX Deployment Verification\n")

        # Backend health
        try:
            r = await client.get(f"{BACKEND_URL}/health")
            print(f"✅ Backend health: {r.json().get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ Backend health: {e}")

        # API docs
        try:
            r = await client.get(f"{BACKEND_URL}/docs")
            print(f"✅ API docs: {'available' if r.status_code == 200 else 'unavailable'}")
        except:
            print("❌ API docs unavailable")

        # Frontend
        try:
            r = await client.get(FRONTEND_URL)
            print(f"✅ Frontend: {'available' if r.status_code == 200 else 'unavailable'}")
        except:
            print("⚠️ Frontend not running on :3000 (may be behind nginx)")

        # Login test
        try:
            r = await client.post(f"{BACKEND_URL}/api/v1/auth/login", json={
                "username": "admin", "password": "admin123"
            })
            if r.status_code == 200:
                token = r.json()["data"]["access_token"]
                print(f"✅ Login: working")
                headers = {"Authorization": f"Bearer {token}"}

                # Students
                r = await client.get(f"{BACKEND_URL}/api/v1/students", headers=headers)
                count = r.json().get("pagination", {}).get("total", 0)
                print(f"✅ Students API: {count} students found")

                # Devices
                r = await client.get(f"{BACKEND_URL}/api/v1/devices", headers=headers)
                devices = r.json().get("data", [])
                online = sum(1 for d in devices if d.get("is_online"))
                print(f"✅ Devices API: {len(devices)} devices, {online} online")

                # Attendance
                r = await client.get(f"{BACKEND_URL}/api/v1/attendance/stats", headers=headers)
                stats = r.json().get("data", {})
                print(f"✅ Attendance stats: {stats.get('present_today', 0)} present today")

                # Webhooks
                r = await client.get(f"{BACKEND_URL}/api/v1/webhooks", headers=headers)
                webhooks = r.json().get("data", [])
                print(f"✅ Webhooks API: {len(webhooks)} webhooks configured")
            else:
                print(f"⚠️ Login failed (status {r.status_code}) — run seed script")
        except Exception as e:
            print(f"❌ Login test: {e}")

        print("\n📋 Verification complete!")
        print("If any checks failed, see docs/troubleshooting.md")

if __name__ == "__main__":
    asyncio.run(main())


### 26. CI/CD Pipeline (.github/workflows/ci.yml):

name: AttendX CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install poetry
          cd backend && poetry install
      - name: Lint
        run: |
          cd backend
          poetry run ruff check .
          poetry run mypy app/ --ignore-missing-imports

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: attendx_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install poetry
          cd backend && poetry install
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/attendx_test
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-for-ci
          JWT_SECRET: test-jwt-secret
          FERNET_KEY: test-fernet-key-32-chars-long-ok=
        run: |
          cd backend
          poetry run pytest --cov=app --cov-report=xml -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - name: Install pnpm
        run: npm install -g pnpm
      - name: Install dependencies
        run: cd frontend && pnpm install --frozen-lockfile
      - name: Type check
        run: cd frontend && pnpm tsc --noEmit
      - name: Build
        run: cd frontend && pnpm build

  docker-build:
    needs: [lint, test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Build backend
        run: docker build -t attendx-backend:latest backend/
      - name: Build frontend
        run: docker build -t attendx-frontend:latest frontend/


### 27. .dockerignore files:

backend/.dockerignore:
__pycache__
*.pyc
.git
.env
.venv
tests/
*.md
.mypy_cache
.ruff_cache
.pytest_cache
htmlcov/
*.egg-info

frontend/.dockerignore:
node_modules
.git
*.md
dist
.env


=============================================
FINAL VERIFICATION
=============================================

After completing ALL tasks, run:

1. Tests:
   cd backend
   pytest -v --tb=short
   pytest --cov=app --cov-report=term-missing
   # Target: 80%+ coverage

2. Lint:
   ruff check .
   mypy app/ --ignore-missing-imports

3. Docker build:
   cd docker
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d

4. Verify deployment:
   docker-compose exec backend python -m scripts.verify_deployment

5. Check all services:
   docker-compose ps
   curl http://localhost/health
   curl http://localhost/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}'

6. Frontend accessible at http://localhost
7. API docs at http://localhost/docs
8. Login works, dashboard shows data
9. Terminal online in Devices page