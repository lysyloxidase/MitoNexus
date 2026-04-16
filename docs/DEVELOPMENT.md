# Development

## Prerequisites

- Python 3.12+
- `uv`
- Node.js 22+
- `pnpm` 9+
- Docker Desktop or Docker Engine with Compose

## Local Setup

### 1. Install workspace dependencies

```bash
cd apps/backend
uv pip install -e ".[dev]"
cd ../frontend
pnpm install
cd ../..
```

### 2. Start infrastructure

```bash
docker compose up -d --build
```

If default ports are busy, place `MX_*` overrides in a local root `.env` file. This repository
already supports remapped host ports without changing the committed compose file.

### 3. Run the app surfaces

```bash
uv run --directory apps/backend uvicorn mitonexus.main:app --reload
pnpm --filter @mitonexus/frontend dev
```

### 4. Optional end-to-end demo

```bash
uv run --directory apps/backend python scripts/demo.py
```

## Common Tasks

- Backend lint: `uv run --directory apps/backend ruff check .`
- Backend format check: `uv run --directory apps/backend ruff format --check .`
- Backend type-check: `uv run --directory apps/backend mypy src`
- Backend tests: `uv run --directory apps/backend pytest -q`
- Frontend lint: `pnpm --filter @mitonexus/frontend lint`
- Frontend type-check: `pnpm --filter @mitonexus/frontend type-check`
- Frontend tests: `pnpm --filter @mitonexus/frontend test`
- Frontend production build: `pnpm --filter @mitonexus/frontend build`
- Database migrations: `uv run --directory apps/backend alembic upgrade head`

## Quality Gates

1. `uv run --directory apps/backend ruff check .`
2. `uv run --directory apps/backend mypy src`
3. `uv run --directory apps/backend pytest --cov=src --cov-report=term`
4. `pnpm --filter @mitonexus/frontend lint`
5. `pnpm --filter @mitonexus/frontend type-check`
6. `pnpm --filter @mitonexus/frontend test`
7. `docker compose up -d`
8. `curl http://localhost:8000/health`

## Manual Smoke Path

1. Open `http://localhost:3000/analyze`
2. Submit a sample blood panel
3. Wait for the report overview to leave the `processing` state
4. Open `/report/{reportId}/graph`
5. Open `/report/{reportId}/mitochondrion`
6. Download `/api/v1/report/{reportId}/pdf`
