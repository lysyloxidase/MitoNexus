from datetime import date

from mitonexus.schemas.blood_marker import BloodMarkerInput, BloodTestInput
from mitonexus.schemas.cascade import CascadeStatus
from mitonexus.services import CascadeMapper, MarkerEngine


def test_cascade_mapper_flags_transsulfuration_from_homocysteine() -> None:
    blood_test = BloodTestInput(
        patient_age=45,
        patient_sex="M",
        test_date=date(2026, 4, 16),
        markers=[BloodMarkerInput(marker_id="homocysteine", value=19.5, unit="umol/L")],
    )

    marker_results = MarkerEngine().analyze(blood_test)
    assessments = CascadeMapper().assess_cascades(marker_results)
    by_id = {assessment.cascade_id: assessment for assessment in assessments}

    assert by_id["transsulfuration"].status in {
        CascadeStatus.MILDLY_AFFECTED,
        CascadeStatus.MODERATELY_AFFECTED,
        CascadeStatus.SEVERELY_AFFECTED,
    }
    assert "homocysteine" in by_id["transsulfuration"].contributing_markers
    assert "CBS" in by_id["transsulfuration"].affected_genes
