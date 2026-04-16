from enum import StrEnum

from pydantic import BaseModel, Field


class TherapyCategory(StrEnum):
    PHARMACOTHERAPY = "pharmacotherapy"
    TARGETED_MITO_DRUGS = "targeted_mito_drugs"
    SUPPLEMENTATION = "supplementation"
    EXERCISE = "exercise"
    DIET = "diet"
    LIFESTYLE = "lifestyle"


class EvidenceLevel(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class TherapyRecommendation(BaseModel):
    """Structured recommendation with evidence and targeting context."""

    therapy_id: str
    name: str
    category: TherapyCategory
    mechanism_summary: str
    detailed_mechanism: str
    dosage: str
    timing: str | None
    evidence_level: EvidenceLevel
    fda_status: str
    nct_ids: list[str]
    source_pmids: list[str]
    targets_cascades: list[str]
    corrects_markers: list[str]
    contraindications: list[str]
    priority_score: float = Field(..., ge=0, le=100)
