from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MarkerCategory(StrEnum):
    CBC = "complete_blood_count"
    HORMONES = "hormones"
    PROSTATE = "prostate"
    METABOLIC = "metabolic"
    LIVER = "liver"
    KIDNEY = "kidney"
    LIPIDS = "lipids"
    URINALYSIS = "urinalysis"
    VITAMINS = "vitamins"
    ELECTROLYTES = "electrolytes"
    THYROID = "thyroid"
    INFLAMMATION = "inflammation"


class MarkerStatus(StrEnum):
    CRITICALLY_LOW = "critically_low"
    LOW = "low"
    SUBOPTIMAL_LOW = "suboptimal_low"
    OPTIMAL = "optimal"
    SUBOPTIMAL_HIGH = "suboptimal_high"
    HIGH = "high"
    CRITICALLY_HIGH = "critically_high"


class BloodMarkerInput(BaseModel):
    """Single marker entry from the blood-test form."""

    marker_id: str
    value: float
    unit: str


class BloodTestInput(BaseModel):
    """Full blood-test submission."""

    patient_age: int = Field(..., ge=18, le=120)
    patient_sex: Literal["M", "F"]
    test_date: date
    markers: list[BloodMarkerInput]


class MarkerAnalysis(BaseModel):
    """Single analyzed marker with mitochondrial context."""

    marker_id: str
    marker_name: str
    value: float
    unit: str
    reference_min: float | None
    reference_max: float | None
    optimal_min: float | None
    optimal_max: float | None
    status: MarkerStatus
    flag: Literal["\u2191", "\u2193", "\u2713"]
    affected_cascades: list[str]
    affected_genes: list[str]
    affected_kegg_pathways: list[str]
    mito_interpretation: str
    confidence: Literal["high", "medium", "low"]


class RangeBounds(BaseModel):
    """Range bounds for a specific cohort."""

    min: float | None = None
    max: float | None = None


class ReferenceRange(BaseModel):
    """Reference range with optional sex-specific bounds."""

    min: float | None = None
    max: float | None = None
    sex_specific: bool = False
    male: RangeBounds | None = None
    female: RangeBounds | None = None


class OptimalRange(BaseModel):
    """Optimal range with optional sex-specific bounds."""

    min: float | None = None
    max: float | None = None
    sex_specific: bool = False
    male: RangeBounds | None = None
    female: RangeBounds | None = None


class MarkerInterpretationDefinition(BaseModel):
    """Status-specific mitochondrial interpretation."""

    mito_impact: str
    priority_therapies: list[str] = Field(default_factory=list)


class MarkerDefinition(BaseModel):
    """Marker catalog entry loaded from `markers.json`."""

    id: str
    name: str
    category: MarkerCategory
    unit_si: str
    unit_conventional: str
    conversion_factor: float
    reference_range: ReferenceRange
    optimal_range: OptimalRange
    mito_cascades: list[str]
    mito_genes: list[str]
    kegg_pathways: list[str]
    mito_mechanism: str
    interpretations: dict[str, MarkerInterpretationDefinition]
    derived_from: list[str] = Field(default_factory=list)
    literature_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarkerCatalogCategory(BaseModel):
    """Frontend-friendly category grouping."""

    id: str
    label: str
    markers: list[str]


class AnalysisResponse(BaseModel):
    """Response returned after a blood-test submission."""

    report_id: str
