from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest
from langchain_core.messages import AIMessage

from mitonexus.agents.literature_retrieval import LiteratureRetrievalAgent
from mitonexus.agents.workflow import build_workflow
from mitonexus.models import AnalysisReport, BloodTest, Patient
from mitonexus.services.pdf_report import PDFReportGenerator
from mitonexus.tasks.analysis import _run_analysis_workflow_async


@pytest.mark.anyio
async def test_workflow_integration_persists_completed_report(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    patient = Patient(age=45, sex="M", test_date=datetime(2026, 4, 16, tzinfo=UTC))
    blood_test = BloodTest(
        raw_values={
            "glucose": 6.05,
            "insulin": 16.0,
            "homocysteine": 16.8,
            "vitamin_d": 24.0,
            "ggtp": 36.0,
        },
        derived_values={"homa_ir": 4.3},
    )
    patient.blood_test = blood_test
    report = AnalysisReport(
        patient=patient, status="processing", literature_evidence=[], affected_cascades=[]
    )
    db_session.add_all([patient, report])
    await db_session.commit()

    async def fake_invoke_summary_llm(self, prompt: str, context) -> None:
        del self, prompt, context
        return None

    async def fake_literature_execute(self, state, context):
        del self, state, context
        return {
            "literature_evidence": [
                {
                    "source": "pubmed",
                    "external_id": "12345",
                    "title": "Homocysteine and mitochondrial dysfunction",
                    "pmid": "12345",
                }
            ],
            "completed_agents": ["literature_retrieval"],
            "messages": [AIMessage(content="Retrieved 1 local evidence item.")],
        }

    async def fake_generate(
        self,
        report: AnalysisReport,
        output_path,
    ):
        del self, report
        output_path.write_bytes(b"%PDF-1.4\n%mock\n")
        return output_path

    @asynccontextmanager
    async def fake_workflow_context() -> AsyncIterator[object]:
        yield build_workflow()

    monkeypatch.setattr(
        "mitonexus.agents.base.BaseAgent.invoke_summary_llm",
        fake_invoke_summary_llm,
    )
    monkeypatch.setattr(LiteratureRetrievalAgent, "_execute", fake_literature_execute)
    monkeypatch.setattr(PDFReportGenerator, "generate", fake_generate)
    monkeypatch.setattr("mitonexus.tasks.analysis._workflow_context", fake_workflow_context)

    result = await _run_analysis_workflow_async(
        patient_id=str(patient.id),
        blood_test_id=str(blood_test.id),
        report_id=str(report.id),
    )

    assert result["status"] == "complete"

    await db_session.refresh(report)
    assert report.status == "complete"
    assert report.mitoscore is not None
    assert report.therapy_plan is not None
    assert report.visualization_data is not None
    assert report.pdf_path is not None
