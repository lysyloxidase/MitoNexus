from __future__ import annotations

from itertools import islice
from typing import ClassVar

from mitonexus.agents.base import AgentExecutionContext, BaseAgent
from mitonexus.agents.state import MitoNexusState
from mitonexus.agents.tools import (
    get_publication_details_tool,
    search_clinical_trials_tool,
    search_indexed_publications_tool,
    search_pubmed_tool,
)
from mitonexus.config import get_settings
from mitonexus.schemas.blood_marker import MarkerStatus


class LiteratureRetrievalAgent(BaseAgent):
    """Retrieve evidence from indexed literature and live PubMed."""

    name = "literature_retrieval"
    model_name = get_settings().model_primary
    tools: ClassVar = [
        search_indexed_publications_tool,
        search_pubmed_tool,
        get_publication_details_tool,
        search_clinical_trials_tool,
    ]

    SYSTEM_PROMPT = """You are a literature retrieval specialist.
Summarize the most relevant biomedical evidence for the abnormal markers and affected
mitochondrial cascades. Emphasize publication source, recency, and whether the evidence
supports therapeutic action or mechanistic interpretation."""

    async def _execute(
        self,
        state: MitoNexusState,
        context: AgentExecutionContext,
    ) -> dict[str, object]:
        queries = self._build_queries(state)
        evidence: list[dict[str, object]] = []
        seen_keys: set[str] = set()

        for query in queries:
            indexed_hits = await self.call_tool(
                search_indexed_publications_tool,
                {"query": query, "top_k": 4},
                context,
            )
            evidence.extend(self._deduplicate(indexed_hits, seen_keys))

        if len(evidence) < 4:
            mesh_terms = self._build_mesh_terms(state)
            pubmed_hits = await self.call_tool(
                search_pubmed_tool,
                {"mesh_terms": mesh_terms, "lookback_days": 365},
                context,
            )
            evidence.extend(self._deduplicate(pubmed_hits, seen_keys))

        if any(item["status"] == "severely_affected" for item in self._cascade_statuses(state)):
            trial_hits = await self.call_tool(
                search_clinical_trials_tool,
                {"condition": "mitochondrial dysfunction", "status": "RECRUITING"},
                context,
            )
            evidence.extend(self._deduplicate(trial_hits, seen_keys))

        trimmed_evidence = list(islice(evidence, 12))
        title_values: list[str] = []
        for item in trimmed_evidence[:3]:
            title = item.get("title")
            if isinstance(title, str):
                title_values.append(title)
        titles = ", ".join(title_values)
        fallback_summary = (
            f"Retrieved {len(trimmed_evidence)} evidence items. Top titles: {titles or 'none'}."
        )
        llm_summary = await self.invoke_summary_llm(
            (
                f"{self.SYSTEM_PROMPT}\n\n"
                f"Queries: {queries}\n"
                f"Evidence count: {len(trimmed_evidence)}\n"
                f"Top titles: {titles}"
            ),
            context,
        )

        return {
            "literature_evidence": trimmed_evidence,
            "completed_agents": [self.name],
            "messages": self.build_message(llm_summary or fallback_summary),
        }

    def _build_queries(self, state: MitoNexusState) -> list[str]:
        abnormal_markers = [
            analysis
            for analysis in state["marker_analyses"]
            if analysis.status != MarkerStatus.OPTIMAL
        ]
        if not abnormal_markers:
            return ["mitochondrial dysfunction biomarkers therapeutic reasoning"]

        queries: list[str] = []
        for analysis in abnormal_markers[:3]:
            cascade_terms = " ".join(analysis.affected_cascades[:2])
            queries.append(f"{analysis.marker_name} mitochondria {cascade_terms}".strip())

        for assessment in state["cascade_assessments"][:2]:
            queries.append(f"{assessment.name} mitochondrial therapy")

        return list(dict.fromkeys(query for query in queries if query))

    def _build_mesh_terms(self, state: MitoNexusState) -> list[str]:
        terms = ["Mitochondria"]
        terms.extend(analysis.marker_name for analysis in state["marker_analyses"][:3])
        return list(dict.fromkeys(terms))

    def _cascade_statuses(self, state: MitoNexusState) -> list[dict[str, str]]:
        return [
            {"cascade_id": assessment.cascade_id, "status": assessment.status.value}
            for assessment in state["cascade_assessments"]
        ]

    def _deduplicate(
        self,
        items: object,
        seen_keys: set[str],
    ) -> list[dict[str, object]]:
        if not isinstance(items, list):
            return []

        deduped: list[dict[str, object]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            external_id = item.get("external_id") or item.get("nct_id") or item.get("title")
            if not isinstance(external_id, str) or external_id in seen_keys:
                continue
            seen_keys.add(external_id)
            deduped.append(item)
        return deduped
