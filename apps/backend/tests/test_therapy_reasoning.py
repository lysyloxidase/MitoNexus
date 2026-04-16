from datetime import UTC, datetime

import pytest

from mitonexus.agents.therapy_reasoning import TherapyReasoningAgent
from mitonexus.models import AnalysisReport, Patient
from mitonexus.schemas.blood_marker import BloodMarkerInput, BloodTestInput
from mitonexus.services import CascadeMapper, get_marker_engine


@pytest.mark.anyio
async def test_therapy_reasoning_prioritizes_homocysteine_support(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_invoke_summary_llm(self, prompt: str, context) -> None:
        del self, prompt, context
        return None

    monkeypatch.setattr(
        "mitonexus.agents.base.BaseAgent.invoke_summary_llm",
        fake_invoke_summary_llm,
    )

    patient = Patient(age=46, sex="M", test_date=datetime(2026, 4, 16, tzinfo=UTC))
    report = AnalysisReport(
        patient=patient, status="processing", literature_evidence=[], affected_cascades=[]
    )
    db_session.add_all([patient, report])
    await db_session.commit()

    blood_test_input = BloodTestInput(
        patient_age=46,
        patient_sex="M",
        test_date=datetime(2026, 4, 16, tzinfo=UTC).date(),
        markers=[
            BloodMarkerInput(marker_id="homocysteine", value=16.8, unit="umol/L"),
            BloodMarkerInput(marker_id="glucose", value=109.0, unit="mg/dL"),
            BloodMarkerInput(marker_id="insulin", value=16.0, unit="uIU/mL"),
        ],
    )
    marker_analyses = get_marker_engine().analyze(blood_test_input)
    cascade_assessments = CascadeMapper().assess_cascades(marker_analyses)

    agent = TherapyReasoningAgent()
    result = await agent(
        {
            "patient_id": str(patient.id),
            "blood_test_id": "blood-test-1",
            "report_id": str(report.id),
            "messages": [],
            "next_agent": None,
            "completed_agents": [],
            "patient_profile": {"age": 46, "sex": "M", "test_date": "2026-04-16"},
            "raw_values": {},
            "derived_values": {},
            "marker_analyses": marker_analyses,
            "cascade_assessments": cascade_assessments,
            "literature_evidence": [],
            "therapy_recommendations": [],
            "mitoscore": None,
            "visualization_data": None,
            "pdf_path": None,
            "report_summary": None,
        }
    )  # type: ignore[arg-type]

    recommendations = result["therapy_recommendations"]
    assert recommendations
    assert recommendations[0].priority_score >= recommendations[-1].priority_score
    therapy_ids = [recommendation.therapy_id for recommendation in recommendations]
    assert "methyl_b12" in therapy_ids
    assert "methyl_folate" in therapy_ids
