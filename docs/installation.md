# Installation Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm (`npm install -g pnpm`)
- Poetry (`pip install poetry`)
- Docker & Docker Compose

## Setup

### 1. Clone the repository

```bash
git clone <repo-url> AttendX
cd AttendX
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY` — Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- `JWT_SECRET` — Generate with `python -c "import secrets; print(secrets.token_hex(16))"`
- `FERNET_KEY` — Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `TELEGRAM_BOT_TOKEN` — Get from @BotFather on Telegram

### 3. Start infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d db redis
```

### 4. Backend

```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### 6. Full Docker deployment

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Verification

- Health check: `curl http://localhost:8000/health`
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
