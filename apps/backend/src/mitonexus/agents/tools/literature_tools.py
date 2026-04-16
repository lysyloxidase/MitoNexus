from __future__ import annotations

from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool
from sqlalchemy import String, cast, or_, select

from mitonexus.apis import ClinicalTrialsClient, PubMedClient
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import Publication
from mitonexus.services import EmbeddingService


@tool
async def search_indexed_publications(query: str, top_k: int = 5) -> list[dict[str, object]]:
    """Search the local pgvector-backed publication index."""
    embedder = EmbeddingService()
    query_vector = await embedder.embed_single(query)

    async with AsyncSessionLocal() as session:
        results = await session.execute(
            select(Publication)
            .where(Publication.embedding.is_not(None))
            .order_by(Publication.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )
        return [publication.to_summary_dict() for publication in results.scalars().all()]


@tool
async def search_pubmed(
    mesh_terms: list[str],
    lookback_days: int = 365,
) -> list[dict[str, object]]:
    """Search recent PubMed results for the provided MeSH terms."""
    today = datetime.now(UTC)
    from_date = today - timedelta(days=lookback_days)

    async with PubMedClient() as client:
        pmids = await client.search_recent(
            mesh_terms=mesh_terms,
            from_date=from_date.strftime("%Y/%m/%d"),
            to_date=today.strftime("%Y/%m/%d"),
        )
        publications = await client.fetch_abstracts(pmids[:10])

    return [publication.to_detail_dict() for publication in publications]


@tool
async def get_publication_details(identifier: str) -> dict[str, object] | None:
    """Retrieve a stored publication by internal id, external id, or PMID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Publication).where(
                or_(
                    Publication.external_id == identifier,
                    cast(Publication.id, String) == identifier,
                )
            )
        )
        publication = result.scalar_one_or_none()

    return publication.to_detail_dict() if publication is not None else None


@tool
async def search_clinical_trials(
    condition: str,
    status: str = "RECRUITING",
) -> list[dict[str, object]]:
    """Search recent mitochondrial-relevant clinical trials."""
    async with ClinicalTrialsClient() as client:
        trials = await client.search_mito_trials([condition], status=status)

    return [trial.model_dump(mode="json") for trial in trials]


search_indexed_publications_tool = search_indexed_publications
search_pubmed_tool = search_pubmed
get_publication_details_tool = get_publication_details
search_clinical_trials_tool = search_clinical_trials
