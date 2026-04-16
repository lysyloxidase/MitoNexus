from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mitonexus.models import AnalysisReport
from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.schemas.therapy import TherapyCategory, TherapyRecommendation

THERAPY_CATEGORY_ORDER = [
    TherapyCategory.PHARMACOTHERAPY,
    TherapyCategory.TARGETED_MITO_DRUGS,
    TherapyCategory.SUPPLEMENTATION,
    TherapyCategory.EXERCISE,
    TherapyCategory.DIET,
    TherapyCategory.LIFESTYLE,
]

THERAPY_TIMELINES: dict[TherapyCategory, str] = {
    TherapyCategory.PHARMACOTHERAPY: "Review tolerance in 2-4 weeks and labs at 8-12 weeks.",
    TherapyCategory.TARGETED_MITO_DRUGS: "Expect an early response signal in 4-8 weeks.",
    TherapyCategory.SUPPLEMENTATION: "Reassess labs and symptoms after 8-12 weeks.",
    TherapyCategory.EXERCISE: "Progress weekly and review capacity after 6-8 weeks.",
    TherapyCategory.DIET: "Track adherence weekly and reassess biomarkers in 6-8 weeks.",
    TherapyCategory.LIFESTYLE: "Monitor day-to-day recovery and review in 4-6 weeks.",
}


class PDFReportGenerator:
    """Generate a styled PDF report from an AnalysisReport instance."""

    def __init__(self) -> None:
        templates_dir = Path(__file__).resolve().parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "xml", "j2")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._templates_dir = templates_dir

    async def generate(self, report: AnalysisReport, output_path: Path) -> Path:
        """Render the report HTML and write the PDF to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = self.render_html(report)
        css_path = self._templates_dir / "report.css"
        await asyncio.to_thread(self._write_pdf, html, output_path, css_path)
        return output_path

    def render_html(self, report: AnalysisReport) -> str:
        """Render the HTML representation for the report."""
        template = self.env.get_template("report.html.j2")
        return template.render(**self._build_context(report))

    def _build_context(self, report: AnalysisReport) -> dict[str, Any]:
        therapy_plan = report.therapy_plan or {}
        marker_analyses = self._load_models(
            therapy_plan.get("marker_analyses"),
            MarkerAnalysis,
        )
        cascade_assessments = self._load_models(
            therapy_plan.get("cascade_assessments"),
            CascadeAssessment,
        )
        recommendations = self._load_models(
            therapy_plan.get("recommendations"),
            TherapyRecommendation,
        )
        visualization = report.visualization_data or {}
        mitochondrion = self._as_dict(visualization.get("mitochondrion"))
        etc_complexes = self._coerce_list_of_dicts(mitochondrion.get("etc_complexes"))
        executive_summary = str(
            therapy_plan.get("summary")
            or "This report summarizes mitochondrial-relevant marker patterns and a prioritized plan."
        )
        abnormal_markers = [
            analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL
        ]
        abnormal_cascades = [
            assessment
            for assessment in cascade_assessments
            if assessment.status != CascadeStatus.OPTIMAL
        ]

        patient = report.patient
        patient_payload = {
            "id": str(getattr(patient, "id", report.patient_id)),
            "age": getattr(patient, "age", None),
            "sex": getattr(patient, "sex", None),
            "test_date": getattr(patient, "test_date", None),
        }
        mitoscore = float(report.mitoscore or 0.0)
        component_scores = report.mitoscore_components or {}

        return {
            "report_id": str(report.id),
            "patient": patient_payload,
            "generated_at": datetime.now(UTC),
            "mitoscore": mitoscore,
            "mitoscore_chart": self._render_mitoscore_gauge(mitoscore, component_scores),
            "component_scores": sorted(component_scores.items()),
            "executive_summary": executive_summary,
            "top_concerns": self._build_top_concerns(abnormal_markers, abnormal_cascades),
            "strengths": self._build_strengths(marker_analyses, mitoscore),
            "marker_analyses": [analysis.model_dump(mode="json") for analysis in marker_analyses],
            "cascade_assessments": [
                assessment.model_dump(mode="json") for assessment in cascade_assessments
            ],
            "cascade_heatmap": self._render_cascade_heatmap(abnormal_cascades),
            "etc_complexes": etc_complexes,
            "therapy_sections": self._build_therapy_sections(recommendations),
            "monitoring_plan": self._build_monitoring_plan(therapy_plan),
            "all_references": self._build_references(report.literature_evidence, recommendations),
        }

    def _build_top_concerns(
        self,
        abnormal_markers: list[MarkerAnalysis],
        abnormal_cascades: list[CascadeAssessment],
    ) -> list[str]:
        concerns: list[str] = []
        for analysis in abnormal_markers[:4]:
            concerns.append(
                f"{analysis.marker_name} is {analysis.status.value.replace('_', ' ')} and points to "
                f"{analysis.mito_interpretation}"
            )
        for assessment in abnormal_cascades[:3]:
            concerns.append(
                f"{assessment.name} is {assessment.status.value.replace('_', ' ')}: "
                f"{assessment.impact_explanation}"
            )
        if not concerns:
            concerns.append("No high-priority mitochondrial concerns were surfaced in the current panel.")
        return concerns

    def _build_strengths(
        self,
        marker_analyses: list[MarkerAnalysis],
        mitoscore: float,
    ) -> list[str]:
        optimal_markers = [
            analysis.marker_name
            for analysis in marker_analyses
            if analysis.status == MarkerStatus.OPTIMAL
        ][:5]
        strengths: list[str] = []
        if mitoscore >= 70:
            strengths.append(
                "The composite MitoScore suggests preserved mitochondrial reserve across the sampled panel."
            )
        if optimal_markers:
            strengths.append(f"Markers currently sitting in the optimal band: {', '.join(optimal_markers)}.")
        if not strengths:
            strengths.append(
                "Several systems still need attention, but the current panel leaves room for measurable improvement."
            )
        return strengths

    def _build_therapy_sections(
        self,
        recommendations: list[TherapyRecommendation],
    ) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        for category in THERAPY_CATEGORY_ORDER:
            items = [
                {
                    **recommendation.model_dump(mode="json"),
                    "expected_timeline": THERAPY_TIMELINES[category],
                }
                for recommendation in recommendations
                if recommendation.category == category
            ]
            if items:
                sections.append(
                    {
                        "id": category.value,
                        "name": category.value.replace("_", " ").title(),
                        "entries": items,
                    }
                )
        return sections

    def _build_monitoring_plan(self, therapy_plan: dict[str, Any]) -> list[str]:
        raw_monitoring = therapy_plan.get("monitoring_plan")
        if isinstance(raw_monitoring, list):
            monitoring = [str(item) for item in raw_monitoring if isinstance(item, str)]
            if monitoring:
                return monitoring
        return ["Repeat the relevant blood panel in 8-12 weeks to assess response."]

    def _build_references(
        self,
        evidence: list[dict[str, object]],
        recommendations: list[TherapyRecommendation],
    ) -> list[dict[str, str]]:
        references: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for publication in evidence:
            pmid = publication.get("pmid")
            identifier = str(
                pmid
                or publication.get("external_id")
                or publication.get("doi")
                or publication.get("id")
                or ""
            )
            if not identifier:
                continue
            key = ("publication", identifier)
            if key in seen:
                continue
            seen.add(key)
            references.append(
                {
                    "label": (
                        f"PMID {identifier}"
                        if str(publication.get("source", "")).lower() == "pubmed" and pmid
                        else f"{str(publication.get('source', 'literature')).title()} {identifier}"
                    ),
                    "detail": str(publication.get("title") or "Indexed literature evidence"),
                }
            )

        for recommendation in recommendations:
            for pmid in recommendation.source_pmids:
                key = ("pmid", pmid)
                if key in seen:
                    continue
                seen.add(key)
                references.append(
                    {
                        "label": f"PMID {pmid}",
                        "detail": f"Supporting evidence cited for {recommendation.name}.",
                    }
                )
            for nct_id in recommendation.nct_ids:
                key = ("nct", nct_id)
                if key in seen:
                    continue
                seen.add(key)
                references.append(
                    {
                        "label": nct_id,
                        "detail": f"Clinical-trial identifier linked to {recommendation.name}.",
                    }
                )

        if not references:
            references.append(
                {
                    "label": "MitoNexus reference set",
                    "detail": "No external references were attached to this report payload.",
                }
            )

        return references

    def _render_mitoscore_gauge(
        self,
        mitoscore: float,
        component_scores: dict[str, float],
    ) -> str:
        score = max(0.0, min(mitoscore, 100.0))
        circumference = 2 * 3.141592653589793 * 60
        offset = circumference * (1 - (score / 100))
        component_lines = "".join(
            f"""
            <div class="component-chip">
              <span>{label.replace('_', ' ')}</span>
              <strong>{value:.0f}</strong>
            </div>
            """
            for label, value in sorted(component_scores.items())
        )
        return f"""
        <div class="mitoscore-chart">
          <svg viewBox="0 0 180 180" class="mitoscore-gauge" aria-hidden="true">
            <circle cx="90" cy="90" r="60" class="gauge-track"></circle>
            <circle
              cx="90"
              cy="90"
              r="60"
              class="gauge-progress"
              stroke-dasharray="{circumference:.2f}"
              stroke-dashoffset="{offset:.2f}"
            ></circle>
            <text x="90" y="84" text-anchor="middle" class="gauge-label">MitoScore</text>
            <text x="90" y="108" text-anchor="middle" class="gauge-value">{score:.0f}</text>
          </svg>
          <div class="component-chip-grid">{component_lines}</div>
        </div>
        """

    def _render_cascade_heatmap(self, cascades: list[CascadeAssessment]) -> str:
        if not cascades:
            return """
            <div class="empty-heatmap">
              No materially affected cascades were detected from the current report payload.
            </div>
            """

        weights = {
            CascadeStatus.MILDLY_AFFECTED: 0.4,
            CascadeStatus.MODERATELY_AFFECTED: 0.7,
            CascadeStatus.SEVERELY_AFFECTED: 1.0,
            CascadeStatus.OPTIMAL: 0.2,
        }
        rows = "".join(
            f"""
            <div class="heatmap-row">
              <span>{cascade.name}</span>
              <div class="heatmap-bar">
                <div class="heatmap-fill" style="width: {weights[cascade.status] * 100:.0f}%"></div>
              </div>
              <strong>{cascade.status.value.replace('_', ' ')}</strong>
            </div>
            """
            for cascade in cascades[:10]
        )
        return f'<div class="cascade-heatmap">{rows}</div>'

    @staticmethod
    def _load_models(raw_items: object, model: type[Any]) -> list[Any]:
        if not isinstance(raw_items, list):
            return []
        validated: list[Any] = []
        for item in raw_items:
            if isinstance(item, dict):
                validated.append(model.model_validate(item))
        return validated

    @staticmethod
    def _as_dict(value: object) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _coerce_list_of_dicts(value: object) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _write_pdf(html: str, output_path: Path, css_path: Path) -> None:
        try:
            from weasyprint import CSS, HTML

            HTML(string=html).write_pdf(output_path, stylesheets=[CSS(filename=str(css_path))])
            return
        except Exception:
            PDFReportGenerator._write_fallback_pdf(html, output_path)

    @staticmethod
    def _write_fallback_pdf(html: str, output_path: Path) -> None:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        cleaned_html = re.sub(r"</(p|div|section|article|li|h1|h2|h3|tr|br|table|header|footer)>", "\n", html)
        cleaned_html = re.sub(r"<[^>]+>", " ", cleaned_html)
        cleaned_html = unescape(cleaned_html)
        paragraphs = [line.strip() for line in cleaned_html.splitlines() if line.strip()]

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story: list[object] = []
        for line in paragraphs:
            style_name = "Heading2" if line.isupper() or line.startswith("MitoNexus") else "BodyText"
            story.append(Paragraph(line, styles[style_name]))
            story.append(Spacer(1, 6))

        doc.build(story)
