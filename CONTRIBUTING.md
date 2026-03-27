# Contributing to AttendX

## Branch Strategy

- `main` — Production-ready code. Protected branch.
- `develop` — Integration branch for features.
- `feature/*` — Feature branches (e.g., `feature/auth-system`).
- `fix/*` — Bug fix branches (e.g., `fix/login-redirect`).
- `release/*` — Release preparation branches.

## Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature
   ```

2. Make your changes and commit with clear messages.

3. Push and create a Pull Request targeting `develop`.

4. After review and CI passes, merge into `develop`.

5. Periodically, `develop` is merged into `main` for releases.

## Code Style

### Backend (Python)

- Formatter: **Black** (line length 88)
- Linter: **Ruff**
- Type checker: **mypy** (strict mode)
- Run before committing:
  ```bash
  cd backend
  poetry run black .
  poetry run ruff check --fix .
  poetry run mypy .
  ```

### Frontend (TypeScript)

- Linter: **ESLint**
- Run before committing:
  ```bash
  cd frontend
  pnpm lint
  ```

## Pre-commit Hooks

Install pre-commit hooks to automate code quality checks:

```bash
cd backend
poetry run pre-commit install
```

## Testing

```bash
# Backend
cd backend
poetry run pytest

# Frontend
cd frontend
pnpm test
```
