from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from mitonexus.schemas.blood_marker import MarkerAnalysis
from mitonexus.schemas.cascade import CascadeAssessment
from mitonexus.schemas.therapy import TherapyRecommendation


class MitoNexusState(TypedDict):
    """Shared state across the multi-agent workflow."""

    patient_id: str
    blood_test_id: str
    report_id: str

    messages: Annotated[list[BaseMessage], add_messages]

    next_agent: str | None
    completed_agents: Annotated[list[str], add]

    patient_profile: dict[str, object]
    raw_values: dict[str, float]
    derived_values: dict[str, float]

    marker_analyses: list[MarkerAnalysis]
    cascade_assessments: list[CascadeAssessment]
    literature_evidence: list[dict[str, object]]
    therapy_recommendations: list[TherapyRecommendation]

    mitoscore: float | None
    visualization_data: dict[str, object] | None
    pdf_path: str | None
    report_summary: str | None
