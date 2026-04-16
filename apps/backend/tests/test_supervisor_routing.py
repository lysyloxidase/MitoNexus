from langchain_core.messages import HumanMessage

from mitonexus.agents.supervisor import SupervisorAgent


def _base_state() -> dict[str, object]:
    return {
        "patient_id": "patient-1",
        "blood_test_id": "blood-test-1",
        "report_id": "report-1",
        "messages": [HumanMessage(content="Analyze this case")],
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


def test_supervisor_routes_parallel_initial_analysis() -> None:
    route, reasoning = SupervisorAgent.decide_next_agent(_base_state())  # type: ignore[arg-type]
    assert route == "parallel_initial_analysis"
    assert "fans out" in reasoning


def test_supervisor_routes_therapy_when_findings_are_ready() -> None:
    state = _base_state()
    state["marker_analyses"] = [{}]
    state["literature_evidence"] = [{}]
    route, _ = SupervisorAgent.decide_next_agent(state)  # type: ignore[arg-type]
    assert route == "therapy_reasoning"


def test_supervisor_routes_end_when_report_bundle_exists() -> None:
    state = _base_state()
    state["marker_analyses"] = [{}]
    state["literature_evidence"] = [{}]
    state["therapy_recommendations"] = [{}]
    state["mitoscore"] = 82.0
    state["visualization_data"] = {"knowledge_graph": {}}
    state["pdf_path"] = "report.pdf"
    route, _ = SupervisorAgent.decide_next_agent(state)  # type: ignore[arg-type]
    assert route == "END"
