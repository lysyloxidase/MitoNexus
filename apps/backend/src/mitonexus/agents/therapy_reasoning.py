from __future__ import annotations

from collections import defaultdict
from typing import ClassVar

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.agents.tools import (
    check_contraindications_tool,
    check_drug_interactions_tool,
    get_clinical_trials_tool,
    lookup_therapy_tool,
)
from mitonexus.config import get_settings
from mitonexus.schemas.cascade import CascadeStatus
from mitonexus.services import get_marker_engine
from mitonexus.services.therapy_catalog import build_recommendation

CASCADE_SEVERITY_SCORES: dict[CascadeStatus, float] = {
    CascadeStatus.OPTIMAL: 0.0,
    CascadeStatus.MILDLY_AFFECTED: 8.0,
    CascadeStatus.MODERATELY_AFFECTED: 16.0,
    CascadeStatus.SEVERELY_AFFECTED: 24.0,
}

EVIDENCE_SCORES: dict[str, float] = {
    "A": 34.0,
    "B": 26.0,
    "C": 18.0,
    "D": 10.0,
}


class TherapyReasoningAgent(BaseAgent):
    """Generate therapy recommendations with TxAgent-inspired scoring."""

    name = "therapy_reasoning"
    model_name = get_settings().model_reasoner
    temperature = 0.0
    tools: ClassVar = [
        lookup_therapy_tool,
        check_drug_interactions_tool,
        check_contraindications_tool,
        get_clinical_trials_tool,
    ]

    SYSTEM_PROMPT = """You are a therapy reasoning specialist for mitochondrial health.
Prioritize therapies by cascade severity, evidence, safety, and biomarker fit.
Group therapies into pharmacotherapy, targeted mitochondrial drugs, supplementation,
exercise, diet, and lifestyle. Avoid inventing contraindications or trial ids."""

    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        candidate_map = self._collect_candidates(state)
        marker_statuses = {
            f"{analysis.marker_id}_status": analysis.status.value
            for analysis in state["marker_analyses"]
        }

        recommendations = []
        cascade_lookup = {
            assessment.cascade_id: CASCADE_SEVERITY_SCORES[assessment.status]
            for assessment in state["cascade_assessments"]
        }
        for therapy_id, support in candidate_map.items():
            profile = await self.call_tool(lookup_therapy_tool, {"therapy_id": therapy_id}, context)
            contraindication_result = await self.call_tool(
                check_contraindications_tool,
                {
                    "therapy_id": therapy_id,
                    "patient_profile": state["patient_profile"],
                    "marker_statuses": marker_statuses,
                },
                context,
            )
            trial_hits = await self.call_tool(
                get_clinical_trials_tool, {"therapy_id": therapy_id}, context
            )
            priority_score = self._score_candidate(
                support,
                cascade_lookup=cascade_lookup,
                evidence_level=str(profile.get("evidence_level", "D")),
                contraindication_count=len(contraindication_result.get("contraindications", [])),
                trial_count=len(trial_hits) if isinstance(trial_hits, list) else 0,
            )
            recommendations.append(
                build_recommendation(
                    therapy_id,
                    priority_score=priority_score,
                    targets_cascades=sorted(support["cascades"]),
                    corrects_markers=sorted(support["markers"]),
                    contraindications=list(contraindication_result.get("contraindications", [])),
                )
            )

        recommendations.sort(key=lambda item: item.priority_score, reverse=True)
        top_ids = [recommendation.therapy_id for recommendation in recommendations[:8]]
        interaction_summary = await self.call_tool(
            check_drug_interactions_tool,
            {"therapy_ids": top_ids},
            context,
        )
        if interaction_summary.get("risk_level") == "moderate":
            for recommendation in recommendations[:8]:
                recommendation.priority_score = max(recommendation.priority_score - 2.0, 0.0)

        grouped_names = ", ".join(recommendation.name for recommendation in recommendations[:4])
        fallback_summary = f"Ranked {len(recommendations)} therapies. Top recommendations: {grouped_names or 'none'}."
        llm_summary = await self.invoke_summary_llm(
            (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"Candidates: {sorted(candidate_map)}\n"
                f"Top recommendations: {grouped_names}\n"
                f"Interaction risk: {interaction_summary.get('risk_level', 'low')}"
            ),
            context,
        )

        return {
            "therapy_recommendations": recommendations[:16],
            "completed_agents": [self.name],
            "messages": self.build_message(llm_summary or fallback_summary),
        }

    def _collect_candidates(
        self,
        state: MitoNexusState,
    ) -> dict[str, dict[str, set[str]]]:
        candidate_map: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: {"markers": set(), "cascades": set()}
        )
        marker_engine = get_marker_engine()

        for analysis in state["marker_analyses"]:
            definition = marker_engine.get_definition(analysis.marker_id)
            if definition is None or analysis.status.value == "optimal":
                continue
            interpretation = definition.interpretations.get(analysis.status.value)
            if (
                interpretation is None
                and "high" in definition.interpretations
                and "high" in analysis.status.value
            ):
                interpretation = definition.interpretations["high"]
            if (
                interpretation is None
                and "low" in definition.interpretations
                and "low" in analysis.status.value
            ):
                interpretation = definition.interpretations["low"]
            if interpretation is None:
                continue

            for therapy_id in interpretation.priority_therapies:
                candidate_map[therapy_id]["markers"].add(analysis.marker_id)
                candidate_map[therapy_id]["cascades"].update(analysis.affected_cascades)

        for assessment in state["cascade_assessments"]:
            if assessment.status == CascadeStatus.OPTIMAL:
                continue
            for therapy_id in assessment.therapeutic_targets:
                candidate_map[therapy_id]["markers"].update(assessment.contributing_markers)
                candidate_map[therapy_id]["cascades"].add(assessment.cascade_id)

        return candidate_map

    def _score_candidate(
        self,
        support: dict[str, set[str]],
        *,
        cascade_lookup: dict[str, float],
        evidence_level: str,
        contraindication_count: int,
        trial_count: int,
    ) -> float:
        cascade_score = sum(
            cascade_lookup.get(cascade_id, 0.0) for cascade_id in support["cascades"]
        )

        marker_score = min(len(support["markers"]) * 5.0, 20.0)
        evidence_score = EVIDENCE_SCORES.get(evidence_level, 10.0)
        trial_bonus = min(trial_count * 2.5, 8.0)
        penalty = contraindication_count * 8.0
        raw_score = evidence_score + cascade_score + marker_score + trial_bonus - penalty
        return max(min(raw_score, 100.0), 0.0)
