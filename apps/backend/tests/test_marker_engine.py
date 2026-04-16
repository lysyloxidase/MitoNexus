from datetime import date

from mitonexus.schemas.blood_marker import BloodMarkerInput, BloodTestInput, MarkerStatus
from mitonexus.services.marker_engine import MarkerEngine


def _build_blood_test() -> BloodTestInput:
    return BloodTestInput(
        patient_age=38,
        patient_sex="M",
        test_date=date(2026, 4, 16),
        markers=[
            BloodMarkerInput(marker_id="glucose", value=108.0, unit="mg/dL"),
            BloodMarkerInput(marker_id="insulin", value=18.0, unit="uIU/mL"),
            BloodMarkerInput(marker_id="homocysteine", value=18.0, unit="umol/L"),
            BloodMarkerInput(marker_id="vitamin_d", value=25.0, unit="ng/mL"),
            BloodMarkerInput(marker_id="rbc", value=4.2, unit="10^12/L"),
        ],
    )


def test_marker_engine_analyzes_derived_markers_and_conversions() -> None:
    engine = MarkerEngine()

    results = engine.analyze(_build_blood_test())
    by_id = {result.marker_id: result for result in results}

    assert by_id["glucose"].value == 5.99
    assert by_id["glucose"].status == MarkerStatus.HIGH
    assert by_id["homa_ir"].status == MarkerStatus.CRITICALLY_HIGH
    assert by_id["homocysteine"].status == MarkerStatus.HIGH
    assert by_id["vitamin_d"].status == MarkerStatus.SUBOPTIMAL_LOW


def test_marker_engine_uses_sex_specific_ranges() -> None:
    engine = MarkerEngine()
    blood_test = BloodTestInput(
        patient_age=34,
        patient_sex="F",
        test_date=date(2026, 4, 16),
        markers=[BloodMarkerInput(marker_id="rbc", value=4.2, unit="10^12/L")],
    )

    result = engine.analyze(blood_test)[0]

    assert result.marker_id == "rbc"
    assert result.status == MarkerStatus.SUBOPTIMAL_LOW
