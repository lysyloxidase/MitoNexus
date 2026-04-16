def calculate_homa_ir(glucose_mmol_l: float, insulin_mu_ml: float) -> float:
    """Return HOMA-IR = (glucose x insulin) / 22.5."""
    return (glucose_mmol_l * insulin_mu_ml) / 22.5


def calculate_de_ritis(ast: float, alt: float) -> float:
    """Return the De Ritis ratio = AST / ALT."""
    if alt <= 0:
        raise ValueError("ALT must be greater than zero to calculate the De Ritis ratio.")
    return ast / alt


def calculate_non_hdl(total_chol: float, hdl: float) -> float:
    """Return non-HDL cholesterol = total cholesterol - HDL."""
    return total_chol - hdl


def calculate_egfr_ckd_epi(creatinine_mg_dl: float, age: int, sex: str) -> float:
    """Return the CKD-EPI 2021 creatinine-based eGFR estimate."""
    normalized_sex = sex.upper()
    if normalized_sex not in {"M", "F"}:
        raise ValueError("sex must be 'M' or 'F'.")

    kappa = 0.7 if normalized_sex == "F" else 0.9
    alpha = -0.241 if normalized_sex == "F" else -0.302
    sex_multiplier = 1.012 if normalized_sex == "F" else 1.0

    ratio = creatinine_mg_dl / kappa
    min_term = min(ratio, 1.0)
    max_term = max(ratio, 1.0)
    estimate = 142.0 * (min_term**alpha) * (max_term**-1.2) * (0.9938**age) * sex_multiplier
    return float(estimate)
