from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from mitonexus.models import AnalysisReport, Patient
from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus
from mitonexus.schemas.cascade import CascadeAssessment, CascadeStatus
from mitonexus.services.pdf_report import PDFReportGenerator
from mitonexus.services.report_builder import build_mitochondrion_visualization
from mitonexus.services.therapy_catalog import build_recommendation


def build_report() -> AnalysisReport:
    patient = Patient(age=45, sex="M", test_date=datetime(2026, 4, 15, tzinfo=UTC))
    patient.id = uuid4()

    marker = MarkerAnalysis(
        marker_id="homocysteine",
        marker_name="Homocysteine",
        value=14.2,
        unit="umol/L",
        reference_min=5.0,
        reference_max=15.0,
        optimal_min=5.0,
        optimal_max=8.0,
        status=MarkerStatus.HIGH,
        flag="↑",
        affected_cascades=["nrf2_keap1", "uprmt"],
        affected_genes=["MTHFR", "CBS"],
        affected_kegg_pathways=["hsa00270"],
        mito_interpretation="Elevated homocysteine increases oxidative pressure on ETC function.",
        confidence="high",
    )
    cascade = CascadeAssessment(
        cascade_id="nrf2_keap1",
        name="Nrf2 / Keap1",
        status=CascadeStatus.MODERATELY_AFFECTED,
        contributing_markers=["homocysteine"],
        affected_genes=["NFE2L2"],
        kegg_pathway_id="hsa04068",
        impact_explanation="Redox buffering demand is increased by sulfur-handling stress.",
        therapeutic_targets=["glycine_nac", "sulforaphane"],
    )
    recommendation = build_recommendation(
        "coq10",
        priority_score=84,
        targets_cascades=["nrf2_keap1"],
        corrects_markers=["homocysteine"],
    )

    report = AnalysisReport(
        patient=patient,
        status="complete",
        mitoscore=68.4,
        mitoscore_components={
            "oxidative_stress_balance": 61.0,
            "energy_substrate_metabolism": 72.0,
        },
        affected_cascades=["nrf2_keap1"],
        literature_evidence=[
            {
                "source": "pubmed",
                "external_id": "12345678",
                "pmid": "12345678",
                "title": "Homocysteine-mediated oxidative pressure on mitochondria",
            }
        ],
        therapy_plan={
            "summary": "Homocysteine-linked oxidative stress is the dominant signal in this sample.",
            "marker_analyses": [marker.model_dump(mode="json")],
            "cascade_assessments": [cascade.model_dump(mode="json")],
            "recommendations": [recommendation.model_dump(mode="json")],
            "monitoring_plan": ["Repeat homocysteine and B-vitamin status in 8-12 weeks."],
        },
        visualization_data={
            "mitochondrion": build_mitochondrion_visualization([marker], 68.4),
        },
        pdf_path="report.pdf",
    )
    report.id = uuid4()
    return report


def test_pdf_report_render_html_includes_core_sections() -> None:
    report = build_report()

    html = PDFReportGenerator().render_html(report)

    assert "MitoNexus Personalized Mitochondrial Health Report" in html
    assert "Executive Summary" in html
    assert "Comprehensive Marker Analysis" in html
    assert "Electron Transport Chain Status" in html
    assert "Personalized Therapy Plan" in html
    assert "PMID 12345678" in html


@pytest.mark.asyncio
async def test_pdf_report_generate_writes_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    generator = PDFReportGenerator()
    written: dict[str, object] = {}

    def fake_write_pdf(html: str, output_path: Path, css_path: Path) -> None:
        written["html"] = html
        written["output_path"] = output_path
        written["css_path"] = css_path
        output_path.write_bytes(b"%PDF-1.4\n%stub\n")

    monkeypatch.setattr(generator, "_write_pdf", fake_write_pdf)

    output_path = tmp_path / "report.pdf"
    result = await generator.generate(build_report(), output_path)

    assert result == output_path
    assert output_path.exists()
    assert "MitoNexus Personalized Mitochondrial Health Report" in str(written["html"])
