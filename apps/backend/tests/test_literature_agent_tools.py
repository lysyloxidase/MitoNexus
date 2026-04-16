from datetime import UTC, datetime

import pytest

from mitonexus.agents.tools.literature_tools import (
    get_publication_details_tool,
    search_indexed_publications_tool,
)
from mitonexus.models import Publication


@pytest.mark.asyncio
async def test_search_indexed_publications_returns_ranked_publications(
    db_session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publication = Publication(
        source="pubmed",
        external_id="12345",
        doi="10.1000/test",
        title="Homocysteine and mitochondrial stress",
        abstract="A paper about mitochondrial dysfunction and transsulfuration.",
        authors=["Doe"],
        publication_date=datetime(2026, 1, 1, tzinfo=UTC),
        mesh_terms=["Mitochondria"],
        embedding=[0.1] * 768,
        content_hash="abc123",
    )
    db_session.add(publication)
    await db_session.commit()

    async def fake_embed_single(self, text: str) -> list[float]:
        del self, text
        return [0.1] * 768

    monkeypatch.setattr(
        "mitonexus.services.embedding.EmbeddingService.embed_single",
        fake_embed_single,
    )

    results = await search_indexed_publications_tool.ainvoke(
        {"query": "homocysteine mitochondria", "top_k": 1}
    )
    assert len(results) == 1
    assert results[0]["external_id"] == "12345"

    detail = await get_publication_details_tool.ainvoke({"identifier": "12345"})
    assert detail is not None
    assert detail["title"] == "Homocysteine and mitochondrial stress"
