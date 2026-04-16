from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.models import Publication


def make_embedding(x: float, y: float, z: float) -> list[float]:
    return [x, y, z] + ([0.0] * 765)


async def test_pgvector_similarity_search(db_session: AsyncSession) -> None:
    publications = [
        Publication(
            source="pubmed",
            external_id="PMID-201",
            doi=None,
            title="AMPK signaling review",
            abstract="A review of AMPK signaling.",
            authors=["Author One"],
            publication_date=datetime(2024, 1, 1, tzinfo=UTC),
            mesh_terms=["AMPK"],
            embedding=make_embedding(1.0, 0.0, 0.0),
            content_hash="1" * 64,
        ),
        Publication(
            source="pubmed",
            external_id="PMID-202",
            doi=None,
            title="PGC-1a activation study",
            abstract="A study of PGC-1a activation.",
            authors=["Author Two"],
            publication_date=datetime(2024, 1, 2, tzinfo=UTC),
            mesh_terms=["PGC-1a"],
            embedding=make_embedding(0.0, 1.0, 0.0),
            content_hash="2" * 64,
        ),
        Publication(
            source="pubmed",
            external_id="PMID-203",
            doi=None,
            title="Oxidative stress overview",
            abstract="An overview of oxidative stress.",
            authors=["Author Three"],
            publication_date=datetime(2024, 1, 3, tzinfo=UTC),
            mesh_terms=["Oxidative Stress"],
            embedding=make_embedding(0.0, 0.0, 1.0),
            content_hash="3" * 64,
        ),
    ]

    db_session.add_all(publications)
    await db_session.commit()

    query_vector = make_embedding(0.95, 0.05, 0.0)
    nearest_publication = await db_session.scalar(
        select(Publication).order_by(Publication.embedding.cosine_distance(query_vector)).limit(1)
    )

    assert nearest_publication is not None
    assert nearest_publication.external_id == "PMID-201"
