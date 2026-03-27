# ==============================================================================
# AttendX Backend — Multi-stage Dockerfile
# ==============================================================================

# -- Stage 1: Build ------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
COPY . .

# Install all dependencies directly via pip (bypass poetry lock issues)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.34.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    "asyncpg>=0.31.0" \
    "alembic>=1.14.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.0.0" \
    "python-jose[cryptography]>=3.3.0" \
    "python-multipart>=0.0.18" \
    "redis>=5.0.0" \
    "cryptography>=44.0.0" \
    "python-telegram-bot>=21.0" \
    "httpx>=0.28.0" \
    "structlog>=24.0.0" \
    "tenacity>=9.0.0" \
    "bcrypt>=4.0.0" \
    "openpyxl>=3.1.0" \
    "slowapi>=0.1.9" \
    "reportlab>=4.0.0" \
    "sentry-sdk[fastapi]>=2.0.0"

# -- Stage 2: Runtime ----------------------------------------------------------
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app .

RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
