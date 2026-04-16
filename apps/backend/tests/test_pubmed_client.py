import re
from datetime import UTC, datetime

from pytest_httpx import HTTPXMock

from mitonexus.apis.pubmed import PubMedClient


async def test_pubmed_search_recent_and_fetch_abstracts(httpx_mock: HTTPXMock) -> None:
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
                <ArticleTitle>Mitochondrial signaling in disease</ArticleTitle>
                <Abstract>
                  <AbstractText Label="Background">Mitochondria coordinate stress signals.</AbstractText>
                </Abstract>
                <Journal>
                  <JournalIssue>
                    <PubDate>
                      <Year>2025</Year>
                      <Month>02</Month>
                      <Day>11</Day>
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
              <MeshHeadingList>
                <MeshHeading>
                  <DescriptorName>Mitochondria</DescriptorName>
                </MeshHeading>
              </MeshHeadingList>
            </MedlineCitation>
            <PubmedData>
              <ArticleIdList>
                <ArticleId IdType="doi">10.1000/test-doi</ArticleId>
              </ArticleIdList>
            </PubmedData>
          </PubmedArticle>
        </PubmedArticleSet>
        """,
    )

    async with PubMedClient() as client:
        pmids = await client.search_recent(["Mitochondria"], "2025/01/01", "2025/02/28")
        publications = await client.fetch_abstracts(pmids)

    assert pmids == ["12345"]
    assert len(publications) == 1
    publication = publications[0]
    assert publication.source == "pubmed"
    assert publication.external_id == "12345"
    assert publication.doi == "10.1000/test-doi"
    assert publication.authors == ["Ada Lovelace"]
    assert publication.mesh_terms == ["Mitochondria"]
    assert publication.publication_date == datetime(2025, 2, 11, tzinfo=UTC)
