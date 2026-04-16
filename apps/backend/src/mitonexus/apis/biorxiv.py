from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from mitonexus.apis.base import BaseAPIClient
from mitonexus.models import Publication


class BioRxivClient(BaseAPIClient):
    """bioRxiv and medRxiv preprint API client."""

    base_url = "https://api.biorxiv.org"
    rate_limit_per_second = 1.0

    async def fetch_recent(
        self,
        server: Literal["biorxiv", "medrxiv"],
        from_date: str,
        to_date: str,
    ) -> list[Publication]:
        """Fetch recent preprints between two dates with cursor pagination."""
        cursor = 0
        publications: list[Publication] = []

        while True:
            response = await self._request(
                "GET",
                f"/details/{server}/{from_date}/{to_date}/{cursor}",
            )
            payload = response.json()
            collection = payload.get("collection", [])
            if not collection:
                break

            for item in collection:
                identifier = str(item.get("doi") or item.get("rel_doi") or "")
                title = str(item.get("title") or "").strip()
                if not identifier or not title:
                    continue

                abstract = str(item.get("abstract") or "").strip() or None
                author_text = str(item.get("authors") or "")
                publications.append(
                    Publication(
                        source=server,
                        external_id=identifier,
                        doi=identifier,
                        title=title,
                        abstract=abstract,
                        authors=self._parse_authors(author_text),
                        publication_date=self._parse_date(item.get("date")),
                        mesh_terms=[],
                        embedding=None,
                        content_hash="",
                    )
                )

            cursor += len(collection)
            if len(collection) < 100:
                break

        return publications

    def _parse_authors(self, author_text: str) -> list[str]:
        return [
            author.strip() for author in author_text.replace(";", ",").split(",") if author.strip()
        ]

    def _parse_date(self, raw_date: object) -> datetime | None:
        if not isinstance(raw_date, str) or not raw_date:
            return None
        return datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=UTC)
