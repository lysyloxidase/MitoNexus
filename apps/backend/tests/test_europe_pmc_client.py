import re
from datetime import UTC, datetime

from pytest_httpx import HTTPXMock

from mitonexus.apis.europe_pmc import EuropePMCClient


async def test_europe_pmc_search(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://www\.ebi\.ac\.uk/europepmc/webservices/rest/search"),
        json={
            "resultList": {
                "result": [
                    {
                        "id": "PMC123456",
                        "doi": "10.1000/europepmc",
                        "title": "Europe PMC mitochondrial paper",
                        "abstractText": "Europe PMC abstract.",
                        "authorString": "Ada Lovelace, Grace Hopper",
                        "firstPublicationDate": "2024-07-01",
                    }
                ]
            },
            "nextCursorMark": "AoIIPzM0NDI",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://www\.ebi\.ac\.uk/europepmc/webservices/rest/search"),
        json={"resultList": {"result": []}, "nextCursorMark": "AoIIPzM0NDI"},
    )

    async with EuropePMCClient() as client:
        publications = await client.search('"mitochondria"')

    assert len(publications) == 1
    publication = publications[0]
    assert publication.source == "europepmc"
    assert publication.external_id == "PMC123456"
    assert publication.authors == ["Ada Lovelace", "Grace Hopper"]
    assert publication.publication_date == datetime(2024, 7, 1, tzinfo=UTC)
