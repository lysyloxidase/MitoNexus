# Deployment

## Recommended Production Topology

- Next.js frontend behind a reverse proxy
- FastAPI backend as a separate service
- Celery worker and Celery Beat as background services
- Postgres with pgvector enabled
- Redis for Celery
- Neo4j for graph relationships
- Ollama or a compatible local model host on GPU-capable infrastructure
- Langfuse for trace collection

## Environment Variables

Document the production values for every `MITONEXUS_*` variable in `.env.example`, especially:

- database URLs
- Redis URL
- Neo4j credentials
- Ollama host
- model names
- Langfuse keys
- CORS origins
- frontend URL
- report output directory

## Deployment Checklist

1. Run database migrations: `alembic upgrade head`
2. Verify Ollama models are present:
   - `qwen2.5:7b`
   - `qwen2.5:14b`
   - `deepseek-r1:14b`
   - `nomic-embed-text`
3. Start API, worker, beat, and frontend
4. Confirm `/health`
5. Submit a smoke-test blood panel
6. Confirm:
   - report completes
   - PDF downloads
   - graph view renders
   - mitochondrion view renders
   - Langfuse receives traces

## PDF Runtime Notes

WeasyPrint needs native rendering libraries in the backend image. The Dockerfile in this repository
installs the required Cairo, Pango, Harfbuzz, and font-related packages for Linux containers.

## Security Checklist

- Keep secrets only in deployment-time environment variables or secret managers
- Restrict CORS to trusted frontend origins
- Keep Postgres, Redis, and Neo4j off public networks unless explicitly proxied
- Run containers with least privilege and controlled volumes
- Review generated reports as sensitive health-related artifacts
