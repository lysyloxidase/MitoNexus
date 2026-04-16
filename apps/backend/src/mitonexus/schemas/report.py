from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from mitonexus.schemas.blood_marker import MarkerAnalysis
from mitonexus.schemas.cascade import CascadeAssessment


class AnalysisReportPayload(BaseModel):
    """Serializable analysis report returned by the API."""

    report_id: UUID
    patient_id: UUID
    mitoscore: float | None
    mitoscore_components: dict[str, float] | None
    affected_cascades: list[str] = Field(default_factory=list)
    marker_analyses: list[MarkerAnalysis] = Field(default_factory=list)
    cascade_assessments: list[CascadeAssessment] = Field(default_factory=list)
    therapy_plan: dict[str, Any] | None = None
    pdf_path: str | None = None
    visualization_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
