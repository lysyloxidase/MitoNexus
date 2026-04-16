from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.db.session import get_session
from mitonexus.models import AnalysisReport, BloodTest, Patient
from mitonexus.schemas.blood_marker import (
    AnalysisResponse,
    BloodTestInput,
    MarkerDefinition,
)
from mitonexus.schemas.report import ReportStatus
from mitonexus.services import get_marker_engine
from mitonexus.tasks.analysis import run_analysis_workflow

router = APIRouter(prefix="/api/v1/blood-test", tags=["blood-test"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_blood_test(
    blood_test_input: BloodTestInput,
    session: SessionDep,
) -> AnalysisResponse:
    """Persist the submission and trigger the multi-agent workflow."""
    marker_engine = get_marker_engine()
    normalized_markers = marker_engine.normalize_markers(blood_test_input)
    derived_values = marker_engine.derive_values(normalized_markers)

    patient = Patient(
        age=blood_test_input.patient_age,
        sex=blood_test_input.patient_sex,
        test_date=datetime.combine(blood_test_input.test_date, time.min, tzinfo=UTC),
    )
    patient.blood_test = BloodTest(raw_values=normalized_markers, derived_values=derived_values)

    report = AnalysisReport(
        patient=patient,
        status=ReportStatus.PROCESSING.value,
        literature_evidence=[],
        affected_cascades=[],
        therapy_plan=None,
        visualization_data=None,
        pdf_path=None,
    )
    session.add(patient)
    session.add(report)
    await session.flush()
    await session.commit()

    try:
        async_result = run_analysis_workflow.delay(
            patient_id=str(patient.id),
            blood_test_id=str(patient.blood_test.id),
            report_id=str(report.id),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to dispatch workflow task: {exc}",
        ) from exc

    report.workflow_task_id = async_result.id
    await session.commit()

    return AnalysisResponse(
        report_id=str(report.id),
        task_id=str(async_result.id),
        status=ReportStatus.PROCESSING.value,
    )


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
