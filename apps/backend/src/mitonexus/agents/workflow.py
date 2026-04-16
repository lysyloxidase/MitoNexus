from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from sqlalchemy.engine import make_url

from mitonexus.agents.biomarker_analysis import BiomarkerAnalysisAgent
from mitonexus.agents.literature_retrieval import LiteratureRetrievalAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.agents.supervisor import SupervisorAgent
from mitonexus.agents.synthesis_report import SynthesisReportAgent
from mitonexus.agents.therapy_reasoning import TherapyReasoningAgent
from mitonexus.config import get_settings


def build_workflow(checkpointer: Any | None = None) -> Any:
    """Construct the multi-agent workflow graph."""
    graph = StateGraph(MitoNexusState)

    graph.add_node("supervisor", SupervisorAgent())
    graph.add_node("biomarker_analysis", BiomarkerAnalysisAgent())
    graph.add_node("literature_retrieval", LiteratureRetrievalAgent())
    graph.add_node("therapy_reasoning", TherapyReasoningAgent())
    graph.add_node("synthesis_report", SynthesisReportAgent())

    graph.set_entry_point("supervisor")

    def route_from_supervisor(state: MitoNexusState) -> str | list[str]:
        next_agent = state.get("next_agent")
        if next_agent == "parallel_initial_analysis":
            return ["biomarker_analysis", "literature_retrieval"]
        if next_agent is None or next_agent == "END":
            return END
        return next_agent

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "biomarker_analysis": "biomarker_analysis",
            "literature_retrieval": "literature_retrieval",
            "therapy_reasoning": "therapy_reasoning",
            "synthesis_report": "synthesis_report",
            END: END,
        },
    )

    for agent_name in [
        "biomarker_analysis",
        "literature_retrieval",
        "therapy_reasoning",
        "synthesis_report",
    ]:
        graph.add_edge(agent_name, "supervisor")

    return graph.compile(checkpointer=checkpointer, name="mitonexus_analysis_workflow")


def get_checkpoint_conn_string() -> str:
    """Return a psycopg-compatible connection string for LangGraph checkpointing."""
    url = make_url(str(get_settings().database_url))
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


@asynccontextmanager
async def persistent_workflow() -> AsyncIterator[Any]:
    """Yield a workflow compiled with the Postgres checkpoint saver."""
    async with AsyncPostgresSaver.from_conn_string(get_checkpoint_conn_string()) as checkpointer:
        await checkpointer.setup()
        yield build_workflow(checkpointer=checkpointer)


workflow = build_workflow()
