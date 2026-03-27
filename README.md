# AttendX — Face Recognition Attendance Platform

**AttendX** is a self-hosted, end-to-end attendance management platform that uses
Hikvision face-recognition terminals to record student attendance, provides a
real-time web dashboard, and notifies parents via Telegram.

## Features

| Feature | Details |
|---------|---------|
| Face Recognition | Hikvision ISAPI terminal integration |
| Real-time Dashboard | React + TypeScript — live feed, stats, reports |
| REST API | FastAPI — full OpenAPI at `/docs` |
| Telegram Bot | Uzbek UX — parent notifications, weekly summaries |
| Webhook System | HMAC-signed delivery, circuit breaker, auto-retry |
| Role-based Access | super_admin / admin / teacher / api key |
| Audit Logging | Every mutation tracked with IP and user |
| Security | Brute-force protection, security headers, Sentry |
| Reports | Excel & PDF export |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI 0.115, SQLAlchemy 2.0 async |
| Database | PostgreSQL 15 |
| Cache / Pub-Sub | Redis 7 |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Bot | python-telegram-bot 21 |
| Worker | Async Hikvision ISAPI poller (tenacity retry) |
| Container | Docker + Docker Compose |
| Auth | JWT (python-jose) + API Key (SHA-256 hash) |
| Encryption | Fernet (device passwords) |
| Packaging | Poetry (backend), pnpm (frontend) |

## Project Structure

```
AttendX/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers (auth, students, attendance, …)
│   │   ├── core/            # Security, middleware, permissions, rate limiting
│   │   ├── models/          # SQLAlchemy 2.0 models
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/        # Business logic + webhook engine
│   │   └── main.py          # FastAPI application entry point
│   ├── bot/                 # Telegram bot (python-telegram-bot 21)
│   ├── worker/              # Hikvision ISAPI poller
│   ├── scripts/             # backup.py, restore.py, seed.py
│   ├── tests/               # Pytest async test suite
│   ├── alembic/             # Database migrations
│   └── Dockerfile           # Multi-stage Docker image
├── frontend/
│   ├── src/                 # React application
│   ├── Dockerfile           # Multi-stage Node → nginx image
│   └── nginx.conf           # SPA nginx config
├── docker/
│   ├── docker-compose.yml       # Development
│   ├── docker-compose.prod.yml  # Production (6 services, resource limits)
│   ├── nginx.conf               # Reverse proxy with SSL + rate limiting
│   └── setup-ssl.sh             # Let's Encrypt certificate setup
├── docs/
│   ├── installation-guide.md
│   ├── admin-guide.md
│   ├── api-reference.md
│   ├── troubleshooting.md
│   ├── security-checklist.md
│   ├── postman_collection.json
│   └── systemd/             # Systemd service files for bare-metal deploy
├── .env.example
└── README.md
```

## Quick Start (Development)

### Prerequisites

- Python 3.11+ & Poetry
- Node.js 18+ & pnpm
- Docker & Docker Compose v2

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/attendx.git
cd attendx
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY, JWT_SECRET, FERNET_KEY
```

Generate required secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"   # JWT_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # FERNET_KEY
```

### 2. Start with Docker (recommended)

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.yml exec backend python -m scripts.seed
```

- Dashboard: http://localhost
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Default credentials (from seed): `admin` / `AttendX@2025` — **change immediately.**

### 3. Local Development (no Docker)

```bash
# Backend
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
pnpm install
pnpm dev
```

## Running Tests

```bash
cd backend
poetry run pytest --tb=short -q
```

All tests use SQLite in-memory + FakeRedis — no PostgreSQL or Redis needed.

## Production Deployment

See **[docs/installation-guide.md](docs/installation-guide.md)** for the complete guide.

```bash
# Build production images
docker compose -f docker/docker-compose.prod.yml build

# Start
docker compose -f docker/docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker/docker-compose.prod.yml exec backend alembic upgrade head

# SSL (Let's Encrypt)
bash docker/setup-ssl.sh your-domain.com admin@your-domain.com
```

## API Reference

- Interactive docs: `GET /docs` (Swagger UI)
- ReDoc: `GET /redoc`
- Human-readable: [docs/api-reference.md](docs/api-reference.md)
- Postman collection: [docs/postman_collection.json](docs/postman_collection.json)

## Environment Variables

See [`.env.example`](.env.example) for all variables. Critical production settings:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | 64-char random string |
| `JWT_SECRET` | 32-char random string |
| `FERNET_KEY` | Fernet key for device password encryption |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | `redis://user:pass@host:6379/0` |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `SENTRY_DSN` | Optional — Sentry error tracking |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins |

## Security

See [docs/security-checklist.md](docs/security-checklist.md) for the production
security checklist including firewall, TLS, key rotation, and incident response.

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/installation-guide.md) | Step-by-step production setup |
| [Admin Guide](docs/admin-guide.md) | Day-to-day administration |
| [API Reference](docs/api-reference.md) | All endpoints documented |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and fixes |
| [Security Checklist](docs/security-checklist.md) | Pre-deployment security review |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All PRs require:

- `poetry run pytest` — all tests passing
- `poetry run ruff check .` — no linting errors
- `poetry run mypy app/` — no type errors

## License

[MIT](LICENSE)
