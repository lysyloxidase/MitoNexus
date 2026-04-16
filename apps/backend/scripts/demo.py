# ruff: noqa: T201

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime, time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import AnalysisReport, BloodTest, Patient
from mitonexus.schemas.blood_marker import BloodMarkerInput, BloodTestInput
from mitonexus.services import get_marker_engine
from mitonexus.tasks.analysis import _run_analysis_workflow_async


async def submit_analysis(sample_patient: BloodTestInput) -> tuple[str, str, str]:
    marker_engine = get_marker_engine()
    normalized_markers = marker_engine.normalize_markers(sample_patient)
    derived_values = marker_engine.derive_values(normalized_markers)

    patient = Patient(
        age=sample_patient.patient_age,
        sex=sample_patient.patient_sex,
        test_date=datetime.combine(sample_patient.test_date, time.min, tzinfo=UTC),
    )
    patient.blood_test = BloodTest(raw_values=normalized_markers, derived_values=derived_values)
    report = AnalysisReport(
        patient=patient,
        status="processing",
        literature_evidence=[],
        affected_cascades=[],
        therapy_plan=None,
        visualization_data=None,
        pdf_path=None,
    )

    async with AsyncSessionLocal() as session:
        session.add(patient)
        session.add(report)
        await session.commit()

    blood_test = patient.blood_test
    if blood_test is None:
        raise RuntimeError("Blood test was not created for the demo patient.")

    return str(patient.id), str(blood_test.id), str(report.id)


async def wait_for_completion(patient_id: str, blood_test_id: str, report_id: str) -> None:
    await _run_analysis_workflow_async(
        patient_id=patient_id,
        blood_test_id=blood_test_id,
        report_id=report_id,
    )

    deadline = asyncio.get_running_loop().time() + 120
    while asyncio.get_running_loop().time() < deadline:
        report = await get_report(report_id)
        if report.status == "complete":
            return
        if report.status == "failed":
            raise RuntimeError(report.error_message or "The analysis workflow failed.")
        await asyncio.sleep(0.5)

    raise TimeoutError("Timed out waiting for the demo report to complete.")


async def get_report(report_id: str) -> AnalysisReport:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisReport)
            .options(selectinload(AnalysisReport.patient))
            .where(AnalysisReport.id == UUID(report_id))
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise RuntimeError(f"Report {report_id} was not found.")
        return report


async def get_pdf_path(report_id: str) -> str:
    report = await get_report(report_id)
    if report.pdf_path is None:
        raise RuntimeError("The workflow completed without generating a PDF path.")
    return report.pdf_path


async def main() -> None:
    settings = get_settings()
    sample_patient = BloodTestInput(
        patient_age=45,
        patient_sex="M",
        test_date=date(2026, 4, 15),
        markers=[
            BloodMarkerInput(marker_id="glucose", value=6.1, unit="mmol/L"),
            BloodMarkerInput(marker_id="insulin", value=13, unit="uIU/mL"),
            BloodMarkerInput(marker_id="ft3", value=3.5, unit="pmol/L"),
            BloodMarkerInput(marker_id="vitamin_d", value=42, unit="nmol/L"),
            BloodMarkerInput(marker_id="homocysteine", value=14, unit="umol/L"),
            BloodMarkerInput(marker_id="ast", value=38, unit="U/L"),
            BloodMarkerInput(marker_id="alt", value=28, unit="U/L"),
            BloodMarkerInput(marker_id="ggtp", value=52, unit="U/L"),
            BloodMarkerInput(marker_id="testosterone", value=12, unit="nmol/L"),
            BloodMarkerInput(marker_id="triglycerides", value=2.3, unit="mmol/L"),
            BloodMarkerInput(marker_id="hdl", value=0.95, unit="mmol/L"),
        ],
    )

    patient_id, blood_test_id, report_id = await submit_analysis(sample_patient)
    await wait_for_completion(patient_id, blood_test_id, report_id)

    report = await get_report(report_id)
    summary = ""
    if isinstance(report.therapy_plan, dict):
        summary = str(report.therapy_plan.get("summary") or "")

    print(f"Report ID: {report_id}")
    print(f"MitoScore: {report.mitoscore}/100")
    print(f"Affected cascades: {report.affected_cascades}")
    if summary:
        print(f"Summary: {summary}")

    pdf_path = await get_pdf_path(report_id)
    print(f"PDF: {pdf_path}")
    print(f"Visit: {settings.frontend_url}/report/{report_id}")
    print(f"Visit: {settings.frontend_url}/report/{report_id}/graph")
    print(f"Visit: {settings.frontend_url}/report/{report_id}/mitochondrion")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
