# API

## Core Endpoints

### `GET /health`

Returns the backend liveness payload:

```json
{
  "status": "ok"
}
```

### `POST /api/v1/blood-test/analyze`

Creates a patient, blood test, and pending analysis report, then dispatches the workflow.

Response:

```json
{
  "report_id": "uuid",
  "task_id": "celery-task-id",
  "status": "processing"
}
```

### `GET /api/v1/blood-test/markers`

Returns the full supported marker catalog, including reference ranges and mitochondrial mappings.

### `GET /api/v1/blood-test/marker/{marker_id}`

Returns one marker definition, including cascade, gene, and pathway metadata.

### `GET /api/v1/report/{report_id}`

Returns the report payload used by the UI:

- report lifecycle status
- MitoScore and components
- affected cascades
- literature evidence
- marker and cascade assessments
- therapy plan
- visualization payload
- PDF path

### `GET /api/v1/report/{report_id}/visualization`

Returns:

- `knowledge_graph`
- `mitochondrion`

### `GET /api/v1/report/{report_id}/pdf`

Streams the generated PDF report when available.

## Notes

- Report generation is asynchronous.
- While a workflow is running, the report endpoint returns `status: "processing"`.
- All database queries are routed through SQLAlchemy expressions instead of raw string-concatenated
  SQL.
