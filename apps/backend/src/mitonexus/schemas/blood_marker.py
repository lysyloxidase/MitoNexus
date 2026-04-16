from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class MarkerCategory(StrEnum):
    CBC = "complete_blood_count"
    HORMONES = "hormones"
    METABOLIC = "metabolic"
    LIVER = "liver"
    KIDNEY = "kidney"
    LIPIDS = "lipids"
    URINALYSIS = "urinalysis"
    VITAMINS = "vitamins"
    ELECTROLYTES = "electrolytes"
    THYROID = "thyroid"
    SPECIALIZED = "specialized"


class MarkerStatus(StrEnum):
    CRITICALLY_LOW = "critically_low"
    LOW = "low"
    SUBOPTIMAL_LOW = "suboptimal_low"
    OPTIMAL = "optimal"
    SUBOPTIMAL_HIGH = "suboptimal_high"
    HIGH = "high"
    CRITICALLY_HIGH = "critically_high"


class BloodMarkerInput(BaseModel):
    """Single marker entry from a web form submission."""

    marker_id: str
    value: float
    unit: str


class BloodTestInput(BaseModel):
    """Full blood-test payload captured from the frontend."""

    patient_age: int = Field(..., ge=18, le=120)
    patient_sex: Literal["M", "F"]
    test_date: str
    markers: list[BloodMarkerInput]

    @computed_field
    def marker_count(self) -> int:
        """Return the total number of submitted markers."""
        return len(self.markers)


class MarkerAnalysis(BaseModel):
    """Analysis result for a single blood marker."""

    marker_id: str
    marker_name: str
    value: float
    unit: str
    reference_min: float | None
    reference_max: float | None
    optimal_min: float | None
    optimal_max: float | None
    status: MarkerStatus
    flag: Literal["↑", "↓", "✓"]
    affected_cascades: list[str]
    affected_genes: list[str]
    affected_kegg_pathways: list[str]
    mito_interpretation: str
    confidence: Literal["high", "medium", "low"]
