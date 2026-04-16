from __future__ import annotations

from langchain_core.tools import tool
from sqlalchemy import select

from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import Publication
from mitonexus.services.therapy_catalog import (
    check_interactions,
    get_therapy_profile,
    resolve_contraindications,
)


@tool
async def lookup_therapy(therapy_id: str) -> dict[str, object]:
    """Get a therapy profile from the MitoNexus catalog."""
    profile = get_therapy_profile(therapy_id)
    return {
        "therapy_id": profile.therapy_id,
        "name": profile.name,
        "category": profile.category.value,
        "mechanism_summary": profile.mechanism_summary,
        "detailed_mechanism": profile.detailed_mechanism,
        "dosage": profile.dosage,
        "timing": profile.timing,
        "evidence_level": profile.evidence_level.value,
        "fda_status": profile.fda_status,
        "nct_ids": list(profile.nct_ids),
        "source_pmids": list(profile.source_pmids),
        "contraindications": list(profile.contraindications),
    }


@tool
async def check_drug_interactions(therapy_ids: list[str]) -> dict[str, object]:
    """Check simplified interaction heuristics between therapies."""
    return check_interactions(therapy_ids)


@tool
async def check_contraindications(
    therapy_id: str,
    patient_profile: dict[str, object],
    marker_statuses: dict[str, float | str],
) -> dict[str, object]:
    """Check simplified therapy contraindications against the current profile."""
    contraindications = resolve_contraindications(therapy_id, patient_profile, marker_statuses)
    return {
        "therapy_id": therapy_id,
        "contraindications": contraindications,
        "risk_level": "moderate" if contraindications else "low",
    }


@tool
async def get_clinical_trials(therapy_id: str) -> list[dict[str, object]]:
    """Get locally indexed clinical-trial records associated with a therapy."""
    profile = get_therapy_profile(therapy_id)
    if not profile.nct_ids:
        return []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Publication).where(Publication.external_id.in_(profile.nct_ids))
        )
        return [publication.to_summary_dict() for publication in result.scalars().all()]


lookup_therapy_tool = lookup_therapy
check_drug_interactions_tool = check_drug_interactions
check_contraindications_tool = check_contraindications
get_clinical_trials_tool = get_clinical_trials
