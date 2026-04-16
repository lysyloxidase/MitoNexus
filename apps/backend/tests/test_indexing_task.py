import re
from datetime import UTC, datetime

from pytest_httpx import HTTPXMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mitonexus.models import Publication
from mitonexus.tasks import indexing


class FakeEmbeddingService:
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[float(index)] + ([0.0] * 767) for index, _ in enumerate(texts, start=1)]


async def test_index_pubmed_task_inserts_publications(
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    monkeypatch,
) -> None:
    updated: dict[str, datetime] = {}

    async def fake_get_last_run_timestamp(_source: str, default_window=...):  # type: ignore[no-untyped-def]
        del default_window
        return datetime(2025, 1, 1, tzinfo=UTC)

    async def fake_update_last_run_timestamp(source: str, timestamp: datetime) -> None:
        updated[source] = timestamp

    monkeypatch.setattr(indexing, "EmbeddingService", FakeEmbeddingService)
    monkeypatch.setattr(indexing, "get_last_run_timestamp", fake_get_last_run_timestamp)
    monkeypatch.setattr(indexing, "update_last_run_timestamp", fake_update_last_run_timestamp)

    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://eutils\.ncbi\.nlm\.nih\.gov/entrez/eutils/esearch\.fcgi"),
        json={"esearchresult": {"idlist": ["12345"]}},
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://eutils\.ncbi\.nlm\.nih\.gov/entrez/eutils/efetch\.fcgi"),
        text="""
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <PMID>12345</PMID>
              <Article>
                <ArticleTitle>Mitochondrial quality control</ArticleTitle>
                <Abstract>
                  <AbstractText>Integrated stress response and mitophagy.</AbstractText>
                </Abstract>
                <Journal>
                  <JournalIssue>
                    <PubDate>
                      <Year>2025</Year>
                    </PubDate>
                  </JournalIssue>
                </Journal>
                <AuthorList>
                  <Author>
                    <ForeName>Ada</ForeName>
                    <LastName>Lovelace</LastName>
                  </Author>
                </AuthorList>
              </Article>
            </MedlineCitation>
            <PubmedData>
              <ArticleIdList>
                <ArticleId IdType="doi">10.1000/indexed</ArticleId>
              </ArticleIdList>
            </PubmedData>
          </PubmedArticle>
        </PubmedArticleSet>
        """,
    )

    result = await indexing._index_pubmed_async()

    stored_publications = await db_session.scalars(select(Publication))
    publications = stored_publications.all()

    assert result["indexed"] == 1
    assert len(publications) == 1
    assert publications[0].doi == "10.1000/indexed"
    assert publications[0].embedding is not None
    assert len(list(publications[0].embedding)) == 768
    assert "pubmed" in updated
