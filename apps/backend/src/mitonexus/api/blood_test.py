from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Annotated, Any, Literal, TypedDict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.db.session import get_session
from mitonexus.models import AnalysisReport, BloodTest, Patient
from mitonexus.schemas.blood_marker import (
    AnalysisResponse,
    BloodTestInput,
    MarkerAnalysis,
    MarkerDefinition,
    MarkerStatus,
)
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.schemas.visualization import (
    ETCComplexState,
    GraphEdge,
    GraphNode,
    KnowledgeGraphData,
    MitochondrionVisualization,
)
from mitonexus.services import CascadeMapper, MitoScoreCalculator, get_marker_engine

router = APIRouter(prefix="/api/v1/blood-test", tags=["blood-test"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]

MARKER_STATUS_COLORS: dict[MarkerStatus, str] = {
    MarkerStatus.CRITICALLY_LOW: "#b91c1c",
    MarkerStatus.LOW: "#dc2626",
    MarkerStatus.SUBOPTIMAL_LOW: "#f59e0b",
    MarkerStatus.OPTIMAL: "#10b981",
    MarkerStatus.SUBOPTIMAL_HIGH: "#f59e0b",
    MarkerStatus.HIGH: "#dc2626",
    MarkerStatus.CRITICALLY_HIGH: "#b91c1c",
}

CASCADE_STATUS_COLORS: dict[CascadeStatus, str] = {
    CascadeStatus.OPTIMAL: "#10b981",
    CascadeStatus.MILDLY_AFFECTED: "#f59e0b",
    CascadeStatus.MODERATELY_AFFECTED: "#f97316",
    CascadeStatus.SEVERELY_AFFECTED: "#dc2626",
}

ETC_COMPLEX_MARKERS: dict[str, tuple[str, ...]] = {
    "I": ("homocysteine", "glucose", "ft3"),
    "II": ("uric_acid", "vitamin_d", "potassium"),
    "III": ("ggtp", "non_hdl", "hdl"),
    "IV": ("rbc", "hgb", "de_ritis_ratio"),
    "V": ("insulin", "homa_ir", "potassium"),
}


class TherapyPlanEntry(TypedDict):
    therapy_id: str
    supporting_markers: list[str]
    supporting_cascades: list[str]
    score: int


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_blood_test(
    blood_test_input: BloodTestInput,
    session: SessionDep,
) -> AnalysisResponse:
    """Submit a blood test, persist the analysis, and return a report id."""
    marker_engine = get_marker_engine()
    normalized_markers = marker_engine.normalize_markers(blood_test_input)
    derived_values = marker_engine.derive_values(normalized_markers)
    marker_analyses = marker_engine.analyze(blood_test_input)
    cascade_assessments = CascadeMapper().assess_cascades(marker_analyses)
    mitoscore, mitoscore_components = MitoScoreCalculator().calculate(marker_analyses)
    affected_cascades = [
        cascade.cascade_id
        for cascade in cascade_assessments
        if cascade.status != CascadeStatus.OPTIMAL
    ]

    patient = Patient(
        age=blood_test_input.patient_age,
        sex=blood_test_input.patient_sex,
        test_date=datetime.combine(blood_test_input.test_date, time.min, tzinfo=UTC),
    )
    patient.blood_test = BloodTest(raw_values=normalized_markers, derived_values=derived_values)

    report = AnalysisReport(
        patient=patient,
        mitoscore=mitoscore,
        mitoscore_components=mitoscore_components,
        affected_cascades=affected_cascades,
        therapy_plan=_build_therapy_plan(marker_analyses, cascade_assessments),
        visualization_data=_build_visualization_data(
            marker_analyses,
            cascade_assessments,
            mitoscore,
        ),
    )

    session.add(patient)
    session.add(report)
    await session.flush()

    return AnalysisResponse(report_id=str(report.id))


@router.get("/markers", response_model=list[MarkerDefinition])
async def list_markers() -> list[MarkerDefinition]:
    """Return all supported markers with reference ranges and mito connections."""
    marker_engine = get_marker_engine()
    return sorted(
        marker_engine.definitions.values(),
        key=lambda definition: (definition.category.value, definition.name.lower()),
    )


@router.get("/marker/{marker_id}", response_model=MarkerDefinition)
async def get_marker_detail(marker_id: str) -> MarkerDefinition:
    """Return detailed information for a single marker."""
    definition = get_marker_engine().get_definition(marker_id)
    if definition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown marker '{marker_id}'.",
        )
    return definition


def _build_therapy_plan(
    marker_analyses: list[MarkerAnalysis],
    cascade_assessments: list[CascadeAssessment],
) -> dict[str, object]:
    therapies: dict[str, TherapyPlanEntry] = {}

    abnormal_markers = [analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL]
    for analysis in abnormal_markers:
        definition = get_marker_engine().get_definition(analysis.marker_id)
        if definition is None:
            continue
        interpretation = definition.interpretations.get(analysis.status.value)
        if interpretation is None and analysis.status in {
            MarkerStatus.LOW,
            MarkerStatus.SUBOPTIMAL_LOW,
            MarkerStatus.CRITICALLY_LOW,
        }:
            interpretation = definition.interpretations.get("low")
        if interpretation is None and analysis.status in {
            MarkerStatus.HIGH,
            MarkerStatus.SUBOPTIMAL_HIGH,
            MarkerStatus.CRITICALLY_HIGH,
        }:
            interpretation = definition.interpretations.get("high")
        if interpretation is None:
            interpretation = definition.interpretations.get("optimal")
        if interpretation is None:
            continue

        for therapy_id in interpretation.priority_therapies:
            therapy = therapies.setdefault(
                therapy_id,
                {
                    "therapy_id": therapy_id,
                    "supporting_markers": [],
                    "supporting_cascades": [],
                    "score": 0,
                },
            )
            if analysis.marker_id not in therapy["supporting_markers"]:
                therapy["supporting_markers"].append(analysis.marker_id)
            therapy["score"] += 2

    for cascade in cascade_assessments:
        if cascade.status == CascadeStatus.OPTIMAL:
            continue
        for target in cascade.therapeutic_targets:
            therapy = therapies.setdefault(
                target,
                {
                    "therapy_id": target,
                    "supporting_markers": [],
                    "supporting_cascades": [],
                    "score": 0,
                },
            )
            if cascade.cascade_id not in therapy["supporting_cascades"]:
                therapy["supporting_cascades"].append(cascade.cascade_id)
            therapy["score"] += 1

    prioritized = sorted(
        therapies.values(),
        key=lambda item: item["score"],
        reverse=True,
    )
    return {
        "summary": f"{len(abnormal_markers)} abnormal markers and {len([c for c in cascade_assessments if c.status != CascadeStatus.OPTIMAL])} affected cascades detected.",
        "priority_therapies": prioritized[:8],
        "marker_analyses": [analysis.model_dump(mode="json") for analysis in marker_analyses],
        "cascade_assessments": [assessment.model_dump(mode="json") for assessment in cascade_assessments],
    }


def _build_visualization_data(
    marker_analyses: list[MarkerAnalysis],
    cascade_assessments: list[CascadeAssessment],
    mitoscore: float,
) -> dict[str, Any]:
    abnormal_markers = [analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL]
    abnormal_cascades = [
        assessment for assessment in cascade_assessments if assessment.status != CascadeStatus.OPTIMAL
    ]

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for analysis in abnormal_markers:
        nodes.append(
            GraphNode(
                id=f"marker:{analysis.marker_id}",
                type="marker",
                label=analysis.marker_name,
                centrality=0.55,
                color=MARKER_STATUS_COLORS[analysis.status],
                size=14.0,
                abnormal=True,
                metadata={
                    "marker_id": analysis.marker_id,
                    "status": analysis.status.value,
                    "value": analysis.value,
                    "unit": analysis.unit,
                },
            )
        )

    for assessment in abnormal_cascades:
        nodes.append(
            GraphNode(
                id=f"cascade:{assessment.cascade_id}",
                type="cascade",
                label=assessment.name,
                centrality=0.7,
                color=CASCADE_STATUS_COLORS[assessment.status],
                size=18.0,
                abnormal=True,
                metadata={"status": assessment.status.value},
            )
        )

    node_ids = {node.id for node in nodes}
    for analysis in abnormal_markers:
        for cascade_id in analysis.affected_cascades:
            cascade_node_id = f"cascade:{cascade_id}"
            if cascade_node_id not in node_ids:
                continue
            edges.append(
                GraphEdge(
                    source=f"marker:{analysis.marker_id}",
                    target=cascade_node_id,
                    type="regulation",
                    confidence=0.72,
                    color="#64748b",
                    width=1.8,
                )
            )

    etc_complexes = [
        _build_etc_state("I", marker_analyses),
        _build_etc_state("II", marker_analyses),
        _build_etc_state("III", marker_analyses),
        _build_etc_state("IV", marker_analyses),
        _build_etc_state("V", marker_analyses),
    ]
    mitochondrion = MitochondrionVisualization(
        etc_complexes=etc_complexes,
        overall_health=round(mitoscore, 2),
        annotations=[
            {
                "marker_id": analysis.marker_id,
                "label": analysis.marker_name,
                "status": analysis.status.value,
                "explanation": analysis.mito_interpretation,
            }
            for analysis in abnormal_markers[:10]
        ],
    )
    graph = KnowledgeGraphData(nodes=nodes, edges=edges)

    return {
        "knowledge_graph": graph.model_dump(mode="json"),
        "mitochondrion": mitochondrion.model_dump(mode="json"),
    }


def _build_etc_state(
    complex_id: Literal["I", "II", "III", "IV", "V"],
    marker_analyses: list[MarkerAnalysis],
) -> ETCComplexState:
    relevant_ids = ETC_COMPLEX_MARKERS[complex_id]
    relevant_markers = [analysis for analysis in marker_analyses if analysis.marker_id in relevant_ids]
    abnormal_markers = [analysis for analysis in relevant_markers if analysis.status != MarkerStatus.OPTIMAL]
    activity = max(0.2, 1.0 - (0.18 * len(abnormal_markers)))
    explanation = (
        "No direct marker pressure detected in the available panel."
        if not abnormal_markers
        else f"Influenced by {', '.join(marker.marker_name for marker in abnormal_markers)}."
    )
    return ETCComplexState(
        complex_id=complex_id,
        activity=round(activity, 2),
        contributing_markers=[marker.marker_id for marker in abnormal_markers],
        explanation=explanation,
    )
