# mypy: disable-error-code="untyped-decorator"

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from celery import Task
from redis.asyncio import from_url as redis_from_url

from mitonexus.apis import (
    BioRxivClient,
    ClinicalTrialsClient,
    EuropePMCClient,
    PubMedClient,
    SemanticScholarClient,
)
from mitonexus.config import get_settings
from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import Publication
from mitonexus.schemas import ClinicalTrial, Paper
from mitonexus.services import DeduplicationService, EmbeddingService
from mitonexus.tasks.celery_app import celery_app

MITO_MESH_TERMS = [
    "Mitochondria",
    "Mitochondrial Diseases",
    "Mitochondrial Membrane Transport Proteins",
    "Electron Transport Chain Complex Proteins",
    "Mitochondrial Dynamics",
    "Mitophagy",
    "Mitochondrial Biogenesis",
]

MITO_KEYWORDS = [
    "mitochondria",
    "mitochondrial dysfunction",
    "OXPHOS",
    "ATP synthase",
    "respiratory chain",
    "PGC-1alpha",
    "SIRT3",
    "NAD+",
    "FGF21",
    "GDF15",
    "elamipretide",
    "urolithin",
]

MITO_CONDITIONS = [
    "mitochondrial disease",
    "mitochondrial dysfunction",
    "primary mitochondrial disease",
    "Leigh syndrome",
    "MELAS",
    "mitochondrial myopathy",
]

MITOCARTA_QUERY = "MitoCarta mitochondrial inventory human mitochondria"


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.index_pubmed")
def index_pubmed(self: Task) -> dict[str, int]:
    """Daily PubMed indexing for mitochondrial literature."""
    return _run_with_retry(self, _index_pubmed_async)


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.index_biorxiv")
def index_biorxiv(self: Task) -> dict[str, int]:
    """Daily bioRxiv indexing."""
    return _run_with_retry(self, _index_biorxiv_async)


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.index_medrxiv")
def index_medrxiv(self: Task) -> dict[str, int]:
    """Daily medRxiv indexing."""
    return _run_with_retry(self, _index_medrxiv_async)


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.index_europepmc")
def index_europepmc(self: Task) -> dict[str, int]:
    """Weekly Europe PMC indexing."""
    return _run_with_retry(self, _index_europepmc_async)


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.index_clinical_trials")
def index_clinical_trials(self: Task) -> dict[str, int]:
    """Weekly ClinicalTrials.gov indexing."""
    return _run_with_retry(self, _index_clinical_trials_async)


@celery_app.task(bind=True, max_retries=3, name="mitonexus.tasks.indexing.refresh_mitocarta")
def refresh_mitocarta(self: Task) -> dict[str, int]:
    """Monthly Semantic Scholar sweep for MitoCarta-related literature."""
    return _run_with_retry(self, _refresh_mitocarta_async)


def _run_with_retry(task: Task, async_fn: Any) -> dict[str, int]:
    try:
        return asyncio.run(async_fn())
    except Exception as exc:
        if task.request.retries >= task.max_retries:
            raise
        countdown = min(60, 2 ** (task.request.retries + 1))
        raise task.retry(exc=exc, countdown=countdown) from exc


async def _index_pubmed_async() -> dict[str, int]:
    last_run = await get_last_run_timestamp("pubmed")
    today = datetime.now(UTC)
    dedup = DeduplicationService()
    embedder = EmbeddingService()

    async with PubMedClient() as client:
        pmids = await client.search_recent(
            mesh_terms=MITO_MESH_TERMS,
            from_date=last_run.strftime("%Y/%m/%d"),
            to_date=today.strftime("%Y/%m/%d"),
        )
        new_pmids = await dedup.filter_new(source="pubmed", external_ids=pmids)
        publications = await client.fetch_abstracts(new_pmids)

    stored_count = await embed_and_store(publications, embedder, dedup)
    await update_last_run_timestamp("pubmed", today)
    return {"indexed": stored_count, "skipped": len(pmids) - stored_count}


async def _index_biorxiv_async() -> dict[str, int]:
    return await _index_preprint_source("biorxiv")


async def _index_medrxiv_async() -> dict[str, int]:
    return await _index_preprint_source("medrxiv")


async def _index_preprint_source(source: Literal["biorxiv", "medrxiv"]) -> dict[str, int]:
    last_run = await get_last_run_timestamp(source)
    today = datetime.now(UTC)
    dedup = DeduplicationService()
    embedder = EmbeddingService()

    async with BioRxivClient() as client:
        publications = await client.fetch_recent(
            server=source,
            from_date=last_run.strftime("%Y-%m-%d"),
            to_date=today.strftime("%Y-%m-%d"),
        )

    stored_count = await embed_and_store(publications, embedder, dedup)
    await update_last_run_timestamp(source, today)
    return {"indexed": stored_count, "skipped": max(len(publications) - stored_count, 0)}


async def _index_europepmc_async() -> dict[str, int]:
    last_run = await get_last_run_timestamp("europepmc", default_window=timedelta(days=30))
    today = datetime.now(UTC)
    query = (
        "("
        + " OR ".join(f'"{keyword}"' for keyword in MITO_KEYWORDS)
        + f') AND FIRST_PDATE:[{last_run.date().isoformat()} TO {today.date().isoformat()}]'
    )
    dedup = DeduplicationService()
    embedder = EmbeddingService()

    async with EuropePMCClient() as client:
        publications = await client.search(query)

    stored_count = await embed_and_store(publications, embedder, dedup)
    await update_last_run_timestamp("europepmc", today)
    return {"indexed": stored_count, "skipped": max(len(publications) - stored_count, 0)}


async def _index_clinical_trials_async() -> dict[str, int]:
    today = datetime.now(UTC)
    dedup = DeduplicationService()
    embedder = EmbeddingService()

    async with ClinicalTrialsClient() as client:
        trials = await client.search_mito_trials(MITO_CONDITIONS)

    publications = [clinical_trial_to_publication(trial) for trial in trials]
    stored_count = await embed_and_store(publications, embedder, dedup)
    await update_last_run_timestamp("clinicaltrials", today)
    return {"indexed": stored_count, "skipped": max(len(publications) - stored_count, 0)}


async def _refresh_mitocarta_async() -> dict[str, int]:
    today = datetime.now(UTC)
    dedup = DeduplicationService()
    embedder = EmbeddingService()

    async with SemanticScholarClient() as client:
        papers = await client.search_papers(
            query=MITOCARTA_QUERY,
            fields=["title", "abstract", "authors", "year", "venue", "url", "citationCount", "externalIds"],
        )

    publications = [paper_to_publication(paper) for paper in papers]
    stored_count = await embed_and_store(publications, embedder, dedup)
    await update_last_run_timestamp("mitocarta", today)
    return {"indexed": stored_count, "skipped": max(len(publications) - stored_count, 0)}


async def embed_and_store(
    publications: list[Publication],
    embedder: EmbeddingService,
    dedup: DeduplicationService,
) -> int:
    """Deduplicate, embed, and insert publications into Postgres."""
    new_publications = await dedup.filter_publications(publications)
    if not new_publications:
        return 0

    texts = [
        f"{publication.title}\n\n{publication.abstract or ''}".strip()
        for publication in new_publications
    ]
    embeddings = await embedder.embed_batch(texts)
    for publication, embedding in zip(new_publications, embeddings, strict=True):
        publication.embedding = embedding

    async with AsyncSessionLocal() as session:
        session.add_all(new_publications)
        await session.commit()

    return len(new_publications)


async def get_last_run_timestamp(
    source: str,
    default_window: timedelta = timedelta(days=7),
) -> datetime:
    """Read the last successful run timestamp from Redis."""
    settings = get_settings()
    redis = redis_from_url(str(settings.redis_url), decode_responses=True)
    try:
        value = await redis.get(f"mitonexus:index:last_run:{source}")
    finally:
        await redis.close()

    if not value:
        return datetime.now(UTC) - default_window
    return datetime.fromisoformat(value)


async def update_last_run_timestamp(source: str, timestamp: datetime) -> None:
    """Persist the last successful run timestamp to Redis."""
    settings = get_settings()
    redis = redis_from_url(str(settings.redis_url), decode_responses=True)
    try:
        await redis.set(f"mitonexus:index:last_run:{source}", timestamp.isoformat())
    finally:
        await redis.close()


def clinical_trial_to_publication(trial: ClinicalTrial) -> Publication:
    """Convert a normalized clinical trial record into a publication row."""
    summary_parts = [trial.summary or ""]
    if trial.conditions:
        summary_parts.append("Conditions: " + ", ".join(trial.conditions))
    if trial.interventions:
        summary_parts.append("Interventions: " + ", ".join(trial.interventions))

    return Publication(
        source="clinicaltrials",
        external_id=trial.nct_id,
        doi=None,
        title=trial.title,
        abstract=" ".join(part for part in summary_parts if part).strip() or None,
        authors=["ClinicalTrials.gov"],
        publication_date=trial.start_date,
        mesh_terms=trial.conditions,
        embedding=None,
        content_hash="",
    )


def paper_to_publication(paper: Paper) -> Publication:
    """Convert a Semantic Scholar paper into a publication row."""
    doi = paper.doi or paper.external_ids.get("DOI")
    publication_date = datetime(paper.year, 1, 1, tzinfo=UTC) if paper.year else None
    return Publication(
        source="semanticscholar",
        external_id=paper.paper_id,
        doi=doi,
        title=paper.title,
        abstract=paper.abstract,
        authors=paper.authors,
        publication_date=publication_date,
        mesh_terms=[],
        embedding=None,
        content_hash="",
    )
