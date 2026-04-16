# Development

## Prerequisites

- Python 3.12+
- `uv`
- Node.js 22+
- `pnpm` 9+
- Docker Desktop or Docker Engine with Compose

## Local Setup

### Backend

```bash
cd apps/backend
uv pip install -e ".[dev]"
pytest
```

### Frontend

```bash
cd apps/frontend
pnpm install
pnpm type-check
```

## Common Tasks

- Start local stack: `docker compose up -d --build`
- Stop local stack: `./infrastructure/scripts/dev-down.sh`
- Pull Ollama models: `./infrastructure/docker/ollama/pull-models.sh`
- Lint backend: `cd apps/backend && ruff check . && ruff format --check .`
- Type-check backend: `cd apps/backend && mypy src`
- Lint frontend: `cd apps/frontend && pnpm lint`
- Type-check frontend: `cd apps/frontend && pnpm type-check`
- Run frontend tests: `cd apps/frontend && pnpm test`

## Quality Gates

1. `cd apps/backend && uv pip install -e ".[dev]" && ruff check . && mypy src && pytest`
2. `cd apps/frontend && pnpm install && biome check . && pnpm type-check`
3. `docker compose up -d --build`
4. `curl http://localhost:8000/health`

## Notes

- `seed-db.sh` is a deliberate placeholder until application schemas and fixtures exist.
- `apps/backend/.env` can be created from the root `.env.example` for local, non-Docker runs.
- Docker Compose injects backend service configuration directly for the local stack.
- If default host ports are already occupied, set `MX_*` variables in a root `.env` file to remap
  Docker ports without changing the committed compose file.
