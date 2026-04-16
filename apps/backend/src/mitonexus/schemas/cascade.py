from enum import StrEnum

from pydantic import BaseModel


class CascadeStatus(StrEnum):
    OPTIMAL = "optimal"
    MILDLY_AFFECTED = "mildly_affected"
    MODERATELY_AFFECTED = "moderately_affected"
    SEVERELY_AFFECTED = "severely_affected"


class CascadeAssessment(BaseModel):
    """Status and supporting evidence for a mitochondrial cascade."""

    cascade_id: str
    name: str
    status: CascadeStatus
    contributing_markers: list[str]
    affected_genes: list[str]
    kegg_pathway_id: str | None
    impact_explanation: str
    therapeutic_targets: list[str]
