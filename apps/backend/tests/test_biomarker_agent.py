from datetime import UTC, datetime

import pytest

from mitonexus.agents.biomarker_analysis import BiomarkerAnalysisAgent
from mitonexus.models import AnalysisReport, BloodTest, Patient


class FakeLLM:
    async def ainvoke(self, prompt: str, config: object | None = None) -> object:
        del prompt, config

        class Response:
            content = "Mock biomarker summary"

        return Response()


@pytest.mark.asyncio
async def test_biomarker_agent_generates_marker_and_cascade_assessments(db_session) -> None:
    patient = Patient(age=44, sex="M", test_date=datetime(2026, 4, 16, tzinfo=UTC))
    blood_test = BloodTest(
        raw_values={
            "glucose": 6.05,
            "insulin": 16.0,
            "homocysteine": 16.8,
            "vitamin_d": 24.0,
        },
        derived_values={"homa_ir": 4.3},
    )
    patient.blood_test = blood_test
    report = AnalysisReport(
        patient=patient, status="processing", literature_evidence=[], affected_cascades=[]
    )
    db_session.add_all([patient, report])
    await db_session.commit()

    agent = BiomarkerAnalysisAgent(llm=FakeLLM())
    state = {
        "patient_id": str(patient.id),
        "blood_test_id": str(blood_test.id),
        "report_id": str(report.id),
        "messages": [],
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
    }

    result = await agent(state)  # type: ignore[arg-type]

    analyses = result["marker_analyses"]
    assert isinstance(analyses, list)
    assert any(analysis.marker_id == "homocysteine" for analysis in analyses)
    assert result["cascade_assessments"]
    assert result["completed_agents"] == ["biomarker_analysis"]
    assert result["messages"][0].content == "Mock biomarker summary"
