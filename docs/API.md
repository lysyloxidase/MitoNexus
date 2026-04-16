# API

## Current Endpoints

### `GET /health`

Returns the backend liveness payload used by local development and CI smoke checks.

```json
{
  "status": "ok"
}
```

## Scope

Only the health endpoint exists in Phase 1. Domain APIs, authentication, and data contracts will be
introduced in later phases.
