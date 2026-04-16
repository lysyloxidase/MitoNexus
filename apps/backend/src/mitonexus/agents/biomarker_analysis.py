from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import BloodTest
from mitonexus.schemas.blood_marker import BloodMarkerInput, BloodTestInput, MarkerStatus
from mitonexus.services import CascadeMapper, get_marker_engine


class BiomarkerAnalysisAgent(BaseAgent):
    """Interpret blood markers in mitochondrial context."""

    name = "biomarker_analysis"
    model_name = get_settings().model_primary

    SYSTEM_PROMPT = """You are a biomarker analysis specialist focused on mitochondrial biology.
Summarize the most important abnormal blood markers, their mitochondrial implications,
and the cascades they pressure. Keep it concise and avoid inventing citations."""

    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        blood_test_id = UUID(state["blood_test_id"])
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BloodTest)
                .options(joinedload(BloodTest.patient))
                .where(BloodTest.id == blood_test_id)
            )
            blood_test = result.scalar_one()

        patient = blood_test.patient
        marker_engine = get_marker_engine()
        markers = [
            BloodMarkerInput(
                marker_id=marker_id,
                value=value,
                unit=marker_engine.definitions[marker_id].unit_si,
            )
            for marker_id, value in blood_test.raw_values.items()
            if marker_id in marker_engine.definitions
        ]
        blood_test_input = BloodTestInput(
            patient_age=patient.age,
            patient_sex=patient.sex,
            test_date=date.fromisoformat(patient.test_date.date().isoformat()),
            markers=markers,
        )

        marker_analyses = marker_engine.analyze(blood_test_input)
        cascade_assessments = CascadeMapper().assess_cascades(marker_analyses)
        abnormal_markers = [
            analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL
        ]
        abnormal_names = (
            ", ".join(analysis.marker_name for analysis in abnormal_markers[:4]) or "none"
        )
        fallback_summary = (
            f"Biomarker analysis completed. Key abnormal markers: {abnormal_names}. "
            f"Detected {len(cascade_assessments)} cascade assessments."
        )
        llm_summary = await self.invoke_summary_llm(
            (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"Patient age: {patient.age}\n"
                f"Patient sex: {patient.sex}\n"
                f"Abnormal markers: {abnormal_names}\n"
                f"Cascade count: {len(cascade_assessments)}"
            ),
            context,
        )

        return {
            "patient_profile": {
                "age": patient.age,
                "sex": patient.sex,
                "test_date": patient.test_date.date().isoformat(),
            },
            "raw_values": blood_test.raw_values,
            "derived_values": blood_test.derived_values,
            "marker_analyses": marker_analyses,
            "cascade_assessments": cascade_assessments,
            "completed_agents": [self.name],
            "messages": self.build_message(llm_summary or fallback_summary),
        }
