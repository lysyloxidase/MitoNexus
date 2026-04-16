import re
from datetime import UTC, datetime

from pytest_httpx import HTTPXMock

from mitonexus.apis.biorxiv import BioRxivClient


async def test_biorxiv_fetch_recent(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=re.compile(r"^https://api\.biorxiv\.org/details/biorxiv/2025-01-01/2025-01-31/0"),
        json={
            "messages": [{"status": "ok", "count": 1}],
            "collection": [
                {
                    "doi": "10.1101/2025.01.01.123456",
                    "title": "A mito preprint",
                    "abstract": "Preprint abstract text.",
                    "authors": "Jane Doe; John Smith",
                    "date": "2025-01-15",
                }
            ],
        },
    )

    async with BioRxivClient() as client:
        publications = await client.fetch_recent("biorxiv", "2025-01-01", "2025-01-31")

    assert len(publications) == 1
    publication = publications[0]
    assert publication.source == "biorxiv"
    assert publication.doi == "10.1101/2025.01.01.123456"
    assert publication.authors == ["Jane Doe", "John Smith"]
    assert publication.publication_date == datetime(2025, 1, 15, tzinfo=UTC)
