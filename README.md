# MitoNexus

MitoNexus is a monorepo scaffold for an AI/ML platform focused on personalized mitochondrial health
therapy. Phase 1 establishes the backend and frontend workspaces, local Docker stack, CI workflows,
and developer tooling without implementing product features yet.

## Stack

- Backend: FastAPI, Pydantic Settings, SQLAlchemy, Alembic, Celery
- Frontend: Next.js 15, React 19, Tailwind CSS 4, Biome, Vitest
- Data and infra: Postgres + pgvector, Redis, Neo4j, Ollama, Langfuse
- Tooling: `uv`, `pnpm`, Docker Compose, GitHub Actions

## Quickstart

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health
```

## Repository Map

- `apps/backend`: Python API scaffold and tests
- `apps/frontend`: Next.js application shell
- `packages/shared-types`: shared TypeScript contracts
- `infrastructure`: Docker bootstrap assets and scripts
- `docs`: architecture, development, and API documentation

## Phase 1 Scope

- Monorepo layout
- Dockerized local services
- Backend and frontend quality gates
- CI workflows and editor settings

## License

Released under the MIT License. See [LICENSE](LICENSE).
