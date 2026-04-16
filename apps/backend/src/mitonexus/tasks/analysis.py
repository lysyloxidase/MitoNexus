# mypy: disable-error-code="untyped-decorator"

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from celery import Task
from langchain_core.messages import HumanMessage
from sqlalchemy import select

from mitonexus.agents.workflow import persistent_workflow
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import AnalysisReport
from mitonexus.tasks.celery_app import celery_app
from mitonexus.tasks.runtime import run_async_in_worker


@celery_app.task(bind=True, max_retries=2, name="mitonexus.tasks.analysis.run_analysis_workflow")
def run_analysis_workflow(
    self: Task,
    *,
    patient_id: str,
    blood_test_id: str,
    report_id: str,
) -> dict[str, object]:
    """Run the LangGraph analysis workflow in a Celery worker."""
    try:
        return run_async_in_worker(
            _run_analysis_workflow_async(
                patient_id=patient_id,
                blood_test_id=blood_test_id,
                report_id=report_id,
            )
        )
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            run_async_in_worker(_mark_report_failed(report_id, str(exc)))
            raise
        raise self.retry(exc=exc, countdown=10) from exc


async def _run_analysis_workflow_async(
    *,
    patient_id: str,
    blood_test_id: str,
    report_id: str,
) -> dict[str, object]:
    await _mark_report_processing(report_id)
    async with _workflow_context() as compiled_workflow:
        final_state = await compiled_workflow.ainvoke(
            {
                "patient_id": patient_id,
                "blood_test_id": blood_test_id,
                "report_id": report_id,
                "messages": [
                    HumanMessage(
                        content=(
                            f"Analyze patient {patient_id} for blood test {blood_test_id} "
                            f"and persist report {report_id}."
                        )
                    )
                ],
                "next_agent": None,
                "completed_agents": [],
                "patient_profile": {},
                "raw_values": {},
                "derived_values": {},
                "marker_analyses": [],
                "cascade_assessments": [],
                "literature_evidence": [],
                "therapy_recommendations": [],
                "mitoscore": None,
                "visualization_data": None,
                "pdf_path": None,
                "report_summary": None,
            },
            config={"configurable": {"thread_id": report_id, "checkpoint_ns": "analysis"}},
        )

    return {
        "report_id": report_id,
        "status": "complete",
        "completed_agents": final_state.get("completed_agents", []),
    }


@asynccontextmanager
async def _workflow_context() -> AsyncIterator[Any]:
    async with persistent_workflow() as compiled_workflow:
        yield compiled_workflow


async def _mark_report_processing(report_id: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisReport).where(AnalysisReport.id == UUID(report_id))
        )
        report = result.scalar_one()
        report.status = "processing"
        report.error_message = None
        await session.commit()


async def _mark_report_failed(report_id: str, error_message: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisReport).where(AnalysisReport.id == UUID(report_id))
        )
        report = result.scalar_one_or_none()
        if report is None:
            return
        report.status = "failed"
        report.error_message = error_message[:1000]
        await session.commit()
