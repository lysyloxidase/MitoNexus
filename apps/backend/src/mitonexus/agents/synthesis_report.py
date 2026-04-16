from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import AnalysisReport
from mitonexus.schemas.cascade import CascadeStatus
from mitonexus.services import MitoScoreCalculator
from mitonexus.services.report_builder import (
    build_therapy_plan,
    build_visualization_data,
    generate_report_pdf,
)
from mitonexus.viz import KnowledgeGraphBuilder


class SynthesisReportAgent(BaseAgent):
    """Assemble the final report payload and persist it."""

    name = "synthesis_report"
    model_name = get_settings().model_primary

    SYSTEM_PROMPT = """You are the synthesis agent for MitoNexus.
Write a concise executive summary that combines biomarker findings, literature signals,
therapy priorities, and the overall mitochondrial score without making unsupported claims."""

    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        mitoscore, mitoscore_components = MitoScoreCalculator().calculate(state["marker_analyses"])
        knowledge_graph = await KnowledgeGraphBuilder().build(
            state["marker_analyses"],
            state["cascade_assessments"],
            state["therapy_recommendations"],
        )
        visualization_data = build_visualization_data(
            knowledge_graph,
            state["marker_analyses"],
            mitoscore,
        )
        therapy_plan = build_therapy_plan(
            state["marker_analyses"],
            state["cascade_assessments"],
            state["literature_evidence"],
            state["therapy_recommendations"],
        )
        affected_cascades = [
            assessment.cascade_id
            for assessment in state["cascade_assessments"]
            if assessment.status != CascadeStatus.OPTIMAL
        ]
        fallback_summary = (
            f"MitoScore {mitoscore:.1f}. "
            f"{len(affected_cascades)} cascades were affected and "
            f"{len(state['therapy_recommendations'])} therapies were prioritized."
        )
        llm_summary = await self.invoke_summary_llm(
            (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"MitoScore: {mitoscore}\n"
                f"Affected cascades: {affected_cascades}\n"
                f"Top therapies: {[recommendation.name for recommendation in state['therapy_recommendations'][:5]]}"
            ),
            context,
        )
        summary = llm_summary or fallback_summary
        therapy_plan["summary"] = summary

        settings = get_settings()
        output_dir = Path(settings.report_output_dir)
        patient_age = state["patient_profile"].get("age")
        patient_sex = state["patient_profile"].get("sex")
        patient_test_date = state["patient_profile"].get("test_date")
        pdf_path = generate_report_pdf(
            output_dir=output_dir,
            report_id=state["report_id"],
            patient_age=patient_age if isinstance(patient_age, int) else 0,
            patient_sex=patient_sex if isinstance(patient_sex, str) else "",
            test_date=patient_test_date if isinstance(patient_test_date, str) else "",
            mitoscore=mitoscore,
            affected_cascades=affected_cascades,
            summary=summary,
            markers=state["marker_analyses"],
            therapies=state["therapy_recommendations"],
            evidence=state["literature_evidence"],
        )

        report_id = UUID(state["report_id"])
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AnalysisReport).where(AnalysisReport.id == report_id)
            )
            report = result.scalar_one()
            report.status = "complete"
            report.error_message = None
            report.mitoscore = mitoscore
            report.mitoscore_components = mitoscore_components
            report.affected_cascades = affected_cascades
            report.literature_evidence = state["literature_evidence"]
            report.therapy_plan = therapy_plan
            report.visualization_data = visualization_data
            report.pdf_path = pdf_path
            await session.commit()

        return {
            "mitoscore": mitoscore,
            "visualization_data": visualization_data,
            "pdf_path": pdf_path,
            "report_summary": summary,
            "completed_agents": [self.name],
            "messages": self.build_message(summary),
        }
