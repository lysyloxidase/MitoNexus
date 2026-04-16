from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from jinja2 import Template

from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.schemas.therapy import TherapyRecommendation
from mitonexus.schemas.visualization import (
    ETCComplexState,
    KnowledgeGraphData,
    MitochondrionVisualization,
)

ETC_COMPLEX_MARKERS: dict[str, tuple[str, ...]] = {
    "I": ("homocysteine", "glucose", "ft3"),
    "II": ("uric_acid", "vitamin_d", "potassium"),
    "III": ("ggtp", "non_hdl", "hdl"),
    "IV": ("rbc", "hgb", "de_ritis_ratio"),
    "V": ("insulin", "homa_ir", "potassium"),
}

REPORT_TEMPLATE = Template(
    """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <style>
      body { font-family: Arial, sans-serif; color: #111827; margin: 32px; }
      h1, h2, h3 { margin-bottom: 8px; }
      p { line-height: 1.5; }
      .meta { color: #4b5563; margin-bottom: 24px; }
      .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 20px; }
      .card { border: 1px solid #d1d5db; border-radius: 12px; padding: 14px; }
      .pill { display: inline-block; margin-right: 6px; margin-bottom: 6px; padding: 4px 8px; border-radius: 999px; background: #ecfdf5; color: #065f46; font-size: 12px; }
      table { width: 100%; border-collapse: collapse; margin-top: 12px; }
      th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
      .muted { color: #6b7280; font-size: 12px; }
    </style>
  </head>
  <body>
    <h1>MitoNexus Analysis Report</h1>
    <p class="meta">
      Report ID: {{ report_id }}<br />
      Patient: {{ patient_age }} years, {{ patient_sex }}<br />
      Test date: {{ test_date }}
    </p>

    <div class="grid">
      <div class="card">
        <h2>MitoScore</h2>
        <p>{{ mitoscore }}</p>
      </div>
      <div class="card">
        <h2>Affected cascades</h2>
        {% for cascade in affected_cascades %}
        <span class="pill">{{ cascade }}</span>
        {% endfor %}
      </div>
    </div>

    <h2>Executive summary</h2>
    <p>{{ summary }}</p>

    <h2>Priority therapies</h2>
    <table>
      <thead>
        <tr>
          <th>Therapy</th>
          <th>Category</th>
          <th>Priority</th>
          <th>Mechanism</th>
        </tr>
      </thead>
      <tbody>
        {% for therapy in therapies %}
        <tr>
          <td>{{ therapy.name }}</td>
          <td>{{ therapy.category }}</td>
          <td>{{ therapy.priority_score }}</td>
          <td>{{ therapy.mechanism_summary }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <h2>Key abnormal markers</h2>
    <table>
      <thead>
        <tr>
          <th>Marker</th>
          <th>Status</th>
          <th>Value</th>
          <th>Mito interpretation</th>
        </tr>
      </thead>
      <tbody>
        {% for marker in markers %}
        <tr>
          <td>{{ marker.marker_name }}</td>
          <td>{{ marker.status }}</td>
          <td>{{ marker.value }} {{ marker.unit }}</td>
          <td>{{ marker.mito_interpretation }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <h2>Literature evidence</h2>
    <table>
      <thead>
        <tr>
          <th>Source</th>
          <th>Title</th>
          <th>External ID</th>
        </tr>
      </thead>
      <tbody>
        {% for publication in evidence %}
        <tr>
          <td>{{ publication.source }}</td>
          <td>{{ publication.title }}</td>
          <td>{{ publication.external_id or publication.pmid }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
"""
)


def build_priority_therapy_entries(
    recommendations: list[TherapyRecommendation],
) -> list[dict[str, object]]:
    """Convert full therapy recommendations into compact frontend entries."""
    entries: list[dict[str, object]] = []
    for recommendation in recommendations:
        entries.append(
            {
                "therapy_id": recommendation.therapy_id,
                "supporting_markers": recommendation.corrects_markers,
                "supporting_cascades": recommendation.targets_cascades,
                "score": round(recommendation.priority_score, 2),
            }
        )
    return entries


def build_therapy_plan(
    marker_analyses: list[MarkerAnalysis],
    cascade_assessments: list[CascadeAssessment],
    literature_evidence: list[dict[str, object]],
    recommendations: list[TherapyRecommendation],
) -> dict[str, object]:
    """Build the persisted therapy plan payload."""
    abnormal_markers = [
        analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL
    ]
    abnormal_cascades = [
        assessment
        for assessment in cascade_assessments
        if assessment.status != CascadeStatus.OPTIMAL
    ]
    return {
        "summary": (
            f"{len(abnormal_markers)} abnormal markers and {len(abnormal_cascades)} affected cascades "
            "were synthesized by the multi-agent workflow."
        ),
        "priority_therapies": build_priority_therapy_entries(recommendations[:8]),
        "recommendations": [
            recommendation.model_dump(mode="json") for recommendation in recommendations
        ],
        "literature_evidence": literature_evidence,
        "marker_analyses": [analysis.model_dump(mode="json") for analysis in marker_analyses],
        "cascade_assessments": [
            assessment.model_dump(mode="json") for assessment in cascade_assessments
        ],
        "monitoring_plan": build_monitoring_plan(marker_analyses, recommendations),
    }


def build_monitoring_plan(
    marker_analyses: list[MarkerAnalysis],
    recommendations: list[TherapyRecommendation],
) -> list[str]:
    """Generate a short monitoring checklist from the current findings."""
    monitoring: list[str] = []
    abnormal_ids = {
        analysis.marker_id
        for analysis in marker_analyses
        if analysis.status != MarkerStatus.OPTIMAL
    }

    if {"glucose", "insulin", "homa_ir"} & abnormal_ids:
        monitoring.append("Repeat fasting glucose, fasting insulin, and HOMA-IR in 8-12 weeks.")
    if {"ggtp", "ast", "alt", "de_ritis_ratio"} & abnormal_ids:
        monitoring.append("Trend liver enzymes and review alcohol, medication, and training load.")
    if "homocysteine" in abnormal_ids:
        monitoring.append(
            "Recheck homocysteine with B12, folate, and B6 status after intervention."
        )
    if any(
        recommendation.therapy_id == "vitamin_d_repletion" for recommendation in recommendations
    ):
        monitoring.append("Repeat 25-OH vitamin D and calcium after 8-12 weeks of repletion.")
    if any(
        recommendation.therapy_id in {"potassium_repletion", "magnesium"}
        for recommendation in recommendations
    ):
        monitoring.append("Monitor electrolytes after initiating mineral repletion.")

    if not monitoring:
        monitoring.append(
            "Repeat the relevant blood panel in 8-12 weeks to assess therapy response."
        )
    return monitoring


def build_mitochondrion_visualization(
    marker_analyses: list[MarkerAnalysis],
    mitoscore: float,
) -> dict[str, Any]:
    """Create the patient-specific mitochondrion overlay payload."""
    abnormal_markers = [
        analysis for analysis in marker_analyses if analysis.status != MarkerStatus.OPTIMAL
    ]
    etc_complexes = [
        build_etc_state("I", marker_analyses),
        build_etc_state("II", marker_analyses),
        build_etc_state("III", marker_analyses),
        build_etc_state("IV", marker_analyses),
        build_etc_state("V", marker_analyses),
    ]

    mitochondrion = MitochondrionVisualization(
        etc_complexes=etc_complexes,
        overall_health=round(mitoscore, 2),
        annotations=[
            {
                "marker_id": analysis.marker_id,
                "label": analysis.marker_name,
                "status": analysis.status.value,
                "explanation": analysis.mito_interpretation,
            }
            for analysis in abnormal_markers[:10]
        ],
    )
    return mitochondrion.model_dump(mode="json")


def build_visualization_data(
    knowledge_graph: KnowledgeGraphData,
    marker_analyses: list[MarkerAnalysis],
    mitoscore: float,
) -> dict[str, Any]:
    """Combine graph data with the mitochondrion overlay payload."""
    return {
        "knowledge_graph": knowledge_graph.model_dump(mode="json"),
        "mitochondrion": build_mitochondrion_visualization(marker_analyses, mitoscore),
    }


def build_etc_state(
    complex_id: Literal["I", "II", "III", "IV", "V"],
    marker_analyses: list[MarkerAnalysis],
) -> ETCComplexState:
    """Estimate ETC complex activity from available marker pressure."""
    relevant_ids = ETC_COMPLEX_MARKERS[complex_id]
    relevant_markers = [
        analysis for analysis in marker_analyses if analysis.marker_id in relevant_ids
    ]
    abnormal_markers = [
        analysis for analysis in relevant_markers if analysis.status != MarkerStatus.OPTIMAL
    ]
    activity = max(0.2, 1.0 - (0.18 * len(abnormal_markers)))
    explanation = (
        "No direct marker pressure detected in the available panel."
        if not abnormal_markers
        else f"Influenced by {', '.join(marker.marker_name for marker in abnormal_markers)}."
    )
    return ETCComplexState(
        complex_id=complex_id,
        activity=round(activity, 2),
        contributing_markers=[marker.marker_id for marker in abnormal_markers],
        explanation=explanation,
    )


def generate_report_pdf(
    *,
    output_dir: Path,
    report_id: UUID | str,
    patient_age: int,
    patient_sex: str,
    test_date: str,
    mitoscore: float,
    affected_cascades: list[str],
    summary: str,
    markers: list[MarkerAnalysis],
    therapies: list[TherapyRecommendation],
    evidence: list[dict[str, object]],
) -> str:
    """Render a concise PDF report and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{report_id}.pdf"
    html = REPORT_TEMPLATE.render(
        report_id=str(report_id),
        patient_age=patient_age,
        patient_sex=patient_sex,
        test_date=test_date,
        mitoscore=round(mitoscore, 2),
        affected_cascades=affected_cascades,
        summary=summary,
        markers=markers[:12],
        therapies=therapies[:8],
        evidence=evidence[:10],
    )
    from weasyprint import HTML

    HTML(string=html).write_pdf(pdf_path)
    return str(pdf_path)
