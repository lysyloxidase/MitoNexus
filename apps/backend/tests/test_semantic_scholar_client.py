import re

from pytest_httpx import HTTPXMock

from mitonexus.apis.semantic_scholar import SemanticScholarClient


async def test_semantic_scholar_search(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://api\.semanticscholar\.org/graph/v1/paper/search"),
        json={
            "data": [
                {
                    "paperId": "abc123",
                    "title": "Semantic Scholar mitochondria paper",
                    "abstract": "A semantic scholar abstract.",
                    "externalIds": {"DOI": "10.1000/semantic"},
                    "authors": [{"name": "Ada Lovelace"}],
                    "year": 2024,
                    "venue": "Science",
                    "url": "https://www.semanticscholar.org/paper/abc123",
                    "citationCount": 42,
                }
            ]
        },
    )

    async with SemanticScholarClient() as client:
        papers = await client.search_papers("mitochondria", ["title", "abstract", "authors"])

    assert len(papers) == 1
    paper = papers[0]
    assert paper.paper_id == "abc123"
    assert paper.doi == "10.1000/semantic"
    assert paper.authors == ["Ada Lovelace"]
    assert paper.citation_count == 42
