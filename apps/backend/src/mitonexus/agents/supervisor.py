from __future__ import annotations

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.config import get_settings


class SupervisorAgent(BaseAgent):
    """Route the workflow based on which specialist outputs are missing."""

    name = "supervisor"
    model_name = get_settings().model_router

    SYSTEM_PROMPT = """You are the supervisor agent for MitoNexus.
Choose the next specialist agent based on missing outputs:
- parallel_initial_analysis when biomarkers and literature are both empty
- biomarker_analysis when marker analyses are missing
- literature_retrieval when literature evidence is missing
- therapy_reasoning when therapy recommendations are missing
- synthesis_report when the final report is not assembled
- END when the report is complete

Respond with one short sentence explaining the routing decision."""

    @staticmethod
    def decide_next_agent(state: MitoNexusState) -> tuple[str, str]:
        """Return the next route and a deterministic explanation."""
        if not state["marker_analyses"] and not state["literature_evidence"]:
            return (
                "parallel_initial_analysis",
                "Initial findings and literature evidence are both missing, so the workflow fans out first.",
            )
        if not state["marker_analyses"]:
            return ("biomarker_analysis", "Marker interpretation is still missing.")
        if not state["literature_evidence"]:
            return ("literature_retrieval", "Literature evidence still needs to be gathered.")
        if not state["therapy_recommendations"]:
            return ("therapy_reasoning", "Therapy prioritization has not been generated yet.")
        if (
            state["mitoscore"] is None
            or state["visualization_data"] is None
            or state["pdf_path"] is None
        ):
            return ("synthesis_report", "The final report bundle is incomplete.")
        return ("END", "All required specialist outputs are present.")

    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        next_agent, reasoning = self.decide_next_agent(state)
        llm_reasoning = await self.invoke_summary_llm(
            f"{self.SYSTEM_PROMPT}\n\nCurrent route: {next_agent}\nReasoning: {reasoning}",
            context,
        )
        return {
            "next_agent": next_agent,
            "messages": self.build_message(llm_reasoning or reasoning),
        }
