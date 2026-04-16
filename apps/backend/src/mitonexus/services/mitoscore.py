from dataclasses import dataclass

from mitonexus.schemas.blood_marker import MarkerAnalysis, MarkerStatus


@dataclass(frozen=True)
class ScoreComponent:
    component_id: str
    weight: float
    markers: tuple[str, ...]


COMPONENTS: tuple[ScoreComponent, ...] = (
    ScoreComponent("etc_function", 15.0, ("de_ritis_ratio", "ast", "alt")),
    ScoreComponent("energy_substrate_metabolism", 15.0, ("glucose", "insulin", "homa_ir")),
    ScoreComponent("thyroid_biogenesis_signaling", 12.0, ("ft3", "testosterone", "estradiol")),
    ScoreComponent("oxidative_stress_balance", 12.0, ("ggtp", "uric_acid", "homocysteine")),
    ScoreComponent("mitokine_status", 10.0, ("ast", "alt", "ggtp")),
    ScoreComponent("fatty_acid_oxidation", 10.0, ("triglycerides", "hdl", "non_hdl")),
    ScoreComponent("iron_fe_s_cluster", 8.0, ("rbc", "hgb", "mcv")),
    ScoreComponent("inflammation", 10.0, ("wbc", "neutrophils", "lymphocytes", "homocysteine")),
    ScoreComponent("hematopoiesis_mitophagy", 8.0, ("mcv", "rbc", "hgb", "hct")),
)

STATUS_SCORES: dict[MarkerStatus, float] = {
    MarkerStatus.OPTIMAL: 100.0,
    MarkerStatus.SUBOPTIMAL_LOW: 75.0,
    MarkerStatus.SUBOPTIMAL_HIGH: 75.0,
    MarkerStatus.LOW: 45.0,
    MarkerStatus.HIGH: 45.0,
    MarkerStatus.CRITICALLY_LOW: 15.0,
    MarkerStatus.CRITICALLY_HIGH: 15.0,
}


class MitoScoreCalculator:
    """Compute a weighted mitochondrial health score."""

    def calculate(self, marker_results: list[MarkerAnalysis]) -> tuple[float, dict[str, float]]:
        by_marker = {result.marker_id: result for result in marker_results}
        available_weight = 0.0
        weighted_sum = 0.0
        component_scores: dict[str, float] = {}

        for component in COMPONENTS:
            selected = [by_marker[marker_id] for marker_id in component.markers if marker_id in by_marker]
            if not selected:
                continue

            score = round(
                sum(STATUS_SCORES[result.status] for result in selected) / len(selected),
                2,
            )
            component_scores[component.component_id] = score
            weighted_sum += score * component.weight
            available_weight += component.weight

        if available_weight == 0:
            return 50.0, {}
        return round(weighted_sum / available_weight, 2), component_scores
