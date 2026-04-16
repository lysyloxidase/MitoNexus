from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.models import Publication
from mitonexus.services.dedup import DeduplicationService


def test_content_hash_changes_with_content() -> None:
    dedup = DeduplicationService()

    first_hash = dedup.compute_content_hash("Title", "Abstract", "10.1000/a")
    second_hash = dedup.compute_content_hash("Title", "Abstract changed", "10.1000/a")

    assert first_hash != second_hash


async def test_filter_publications_deduplicates_on_doi(db_session: AsyncSession) -> None:
    dedup = DeduplicationService()
    existing_publication = Publication(
        source="pubmed",
        external_id="123",
        doi="10.1000/duplicate",
        title="Existing title",
        abstract="Existing abstract",
        authors=["Ada Lovelace"],
        publication_date=datetime(2024, 1, 1, tzinfo=UTC),
        mesh_terms=["Mitochondria"],
        embedding=None,
        content_hash=dedup.compute_content_hash("Existing title", "Existing abstract", "10.1000/duplicate"),
    )
    db_session.add(existing_publication)
    await db_session.commit()

    candidate = Publication(
        source="europepmc",
        external_id="PMC999",
        doi="10.1000/duplicate",
        title="Existing title",
        abstract="Existing abstract",
        authors=["Grace Hopper"],
        publication_date=datetime(2024, 1, 2, tzinfo=UTC),
        mesh_terms=[],
        embedding=None,
        content_hash="",
    )

    filtered = await dedup.filter_publications([candidate])

    assert filtered == []
