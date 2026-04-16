from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.db.session import get_session
from mitonexus.models import AnalysisReport as AnalysisReportModel
from mitonexus.schemas.blood_marker import MarkerAnalysis
from mitonexus.schemas.cascade import CascadeAssessment
from mitonexus.schemas.report import AnalysisReportPayload

router = APIRouter(prefix="/api/v1/report", tags=["report"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{report_id}", response_model=AnalysisReportPayload)
async def get_report(
    report_id: UUID,
    session: SessionDep,
) -> AnalysisReportPayload:
    """Return the stored analysis report payload for a report id."""
    report = await _get_report_or_404(session, report_id)
    return _serialize_report(report)


@router.get("/{report_id}/pdf")
async def download_pdf(
    report_id: UUID,
    session: SessionDep,
) -> FileResponse:
    """Return the generated PDF when available."""
    report = await _get_report_or_404(session, report_id)
    if report.pdf_path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF is not available.")

    pdf_path = Path(report.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF file not found.")

    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)


@router.get("/{report_id}/visualization")
async def get_visualization_data(
    report_id: UUID,
    session: SessionDep,
) -> dict[str, object]:
    """Return knowledge-graph and mitochondrion overlay data for 3D rendering."""
    report = await _get_report_or_404(session, report_id)
    return report.visualization_data or {}


async def _get_report_or_404(
    session: AsyncSession,
    report_id: UUID,
) -> AnalysisReportModel:
    result = await session.execute(
        select(AnalysisReportModel).where(AnalysisReportModel.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


def _serialize_report(report: AnalysisReportModel) -> AnalysisReportPayload:
    therapy_plan = report.therapy_plan or {}
    raw_marker_analyses = therapy_plan.get("marker_analyses", [])
    raw_cascade_assessments = therapy_plan.get("cascade_assessments", [])
    marker_items = raw_marker_analyses if isinstance(raw_marker_analyses, list) else []
    cascade_items = raw_cascade_assessments if isinstance(raw_cascade_assessments, list) else []

    marker_analyses = [
        MarkerAnalysis.model_validate(item)
        for item in marker_items
        if isinstance(item, dict)
    ]
    cascade_assessments = [
        CascadeAssessment.model_validate(item)
        for item in cascade_items
        if isinstance(item, dict)
    ]

    public_therapy_plan = {
        key: value
        for key, value in therapy_plan.items()
        if key not in {"marker_analyses", "cascade_assessments"}
    }

    return AnalysisReportPayload(
        report_id=report.id,
        patient_id=report.patient_id,
        mitoscore=report.mitoscore,
        mitoscore_components=report.mitoscore_components,
        affected_cascades=report.affected_cascades,
        marker_analyses=marker_analyses,
        cascade_assessments=cascade_assessments,
        therapy_plan=public_therapy_plan,
        pdf_path=report.pdf_path,
        visualization_data=report.visualization_data,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )
