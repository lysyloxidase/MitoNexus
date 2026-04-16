from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import AnalysisReport
from mitonexus.schemas.cascade import CascadeStatus
from mitonexus.services import MitoScoreCalculator
from mitonexus.services.pdf_report import PDFReportGenerator
from mitonexus.services.report_builder import (
    build_therapy_plan,
    build_visualization_data,
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
        output_dir.mkdir(parents=True, exist_ok=True)
        report_id = UUID(state["report_id"])
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AnalysisReport)
                .options(selectinload(AnalysisReport.patient))
                .where(AnalysisReport.id == report_id)
            )
            report = result.scalar_one()
            pdf_path = output_dir / f"{report.id}.pdf"
            report.status = "processing"
            report.error_message = None
            report.mitoscore = mitoscore
            report.mitoscore_components = mitoscore_components
            report.affected_cascades = affected_cascades
            report.literature_evidence = state["literature_evidence"]
            report.therapy_plan = therapy_plan
            report.visualization_data = visualization_data
            report.pdf_path = str(pdf_path)
            await PDFReportGenerator().generate(report, pdf_path)
            report.status = "complete"
            await session.commit()

        return {
            "mitoscore": mitoscore,
            "visualization_data": visualization_data,
            "pdf_path": str(pdf_path),
            "report_summary": summary,
            "completed_agents": [self.name],
            "messages": self.build_message(summary),
        }
