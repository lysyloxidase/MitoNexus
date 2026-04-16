import pytest

from mitonexus.services.derived_calculations import (
    calculate_de_ritis,
    calculate_egfr_ckd_epi,
    calculate_homa_ir,
    calculate_non_hdl,
)


def test_calculate_homa_ir() -> None:
    assert calculate_homa_ir(5.0, 10.0) == pytest.approx(2.22, rel=1e-2)


def test_calculate_de_ritis() -> None:
    assert calculate_de_ritis(30.0, 20.0) == pytest.approx(1.5)


def test_calculate_de_ritis_raises_for_zero_alt() -> None:
    with pytest.raises(ValueError):
        calculate_de_ritis(20.0, 0.0)


def test_calculate_non_hdl() -> None:
    assert calculate_non_hdl(5.8, 1.4) == pytest.approx(4.4)


def test_calculate_egfr_ckd_epi() -> None:
    estimate = calculate_egfr_ckd_epi(1.0, age=40, sex="M")
    assert 80.0 < estimate < 110.0
