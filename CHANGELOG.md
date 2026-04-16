# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-04-16

### Added

- Monorepo workspace for backend, frontend, shared types, docs, and infrastructure
- Dockerized local stack for Postgres + pgvector, Redis, Neo4j, Ollama, Langfuse, backend, Celery worker, Celery Beat, and Flower
- Backend data layer with SQLAlchemy 2 async models, pgvector storage, Neo4j client, and Alembic migrations
- 41-marker catalog with mitochondrial cascade, gene, and pathway mappings
- Blood-test analysis API, marker catalog endpoints, report endpoints, and persisted report workflow
- Literature indexing clients for PubMed, bioRxiv, medRxiv, Europe PMC, ClinicalTrials.gov, and Semantic Scholar
- Celery Beat schedules for recurring literature ingestion
- LangGraph multi-agent workflow with supervisor, biomarker, literature, therapy, and synthesis agents
- Langfuse-ready tracing hooks for workflow observability
- Next.js blood-test intake form and report overview flow
- 3D knowledge graph visualization with React Three Fiber and `three-forcegraph`
- 3D mitochondrion overlay with a procedural development model and production GLB handoff path
- PDF report generation via Jinja2 and WeasyPrint
- End-to-end backend demo script for seeded patient analysis
- Expanded documentation for architecture, development, API usage, deployment, and end users

### Changed

- Promoted workspace package versions and API metadata to `1.0.0`
- Updated root README from scaffold notes to full product documentation
- Documented all active runtime environment variables in `.env.example`
- Installed native backend image dependencies required for Linux PDF rendering

### Verified

- Backend lint, type-checking, tests, and Alembic migrations
- Frontend lint, type-checking, tests, and production build
- Report payload generation for graph, mitochondrion, and PDF surfaces
