from __future__ import annotations

from datetime import UTC, datetime

from mitonexus.apis.base import BaseAPIClient
from mitonexus.models import Publication


class EuropePMCClient(BaseAPIClient):
    """Europe PMC REST API client."""

    base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    rate_limit_per_second = 2.0

    async def search(self, query: str, page_size: int = 100) -> list[Publication]:
        """Search Europe PMC using cursor-based pagination."""
        cursor_mark = "*"
        publications: list[Publication] = []

        while True:
            response = await self._request(
                "GET",
                "/search",
                params={
                    "query": query,
                    "format": "json",
                    "pageSize": page_size,
                    "resultType": "core",
                    "cursorMark": cursor_mark,
                },
            )
            payload = response.json()
            results = payload.get("resultList", {}).get("result", [])
            if not results:
                break

            for item in results:
                identifier = str(item.get("id") or item.get("pmid") or item.get("doi") or "")
                title = str(item.get("title") or "").strip()
                if not identifier or not title:
                    continue

                publications.append(
                    Publication(
                        source="europepmc",
                        external_id=identifier,
                        doi=self._normalize_text(item.get("doi")),
                        title=title,
                        abstract=self._normalize_text(item.get("abstractText")),
                        authors=self._parse_authors(self._normalize_text(item.get("authorString"))),
                        publication_date=self._parse_publication_date(item),
                        mesh_terms=[],
                        embedding=None,
                        content_hash="",
                    )
                )

            next_cursor = payload.get("nextCursorMark")
            if not isinstance(next_cursor, str) or next_cursor == cursor_mark:
                break
            cursor_mark = next_cursor

        return publications

    def _normalize_text(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _parse_authors(self, author_string: str | None) -> list[str]:
        if author_string is None:
            return []
        return [author.strip() for author in author_string.split(",") if author.strip()]

    def _parse_publication_date(self, item: dict[object, object]) -> datetime | None:
        first_date = item.get("firstPublicationDate")
        if isinstance(first_date, str) and first_date:
            try:
                return datetime.strptime(first_date, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                return None

        pub_year = item.get("pubYear")
        if isinstance(pub_year, str) and pub_year.isdigit():
            return datetime(int(pub_year), 1, 1, tzinfo=UTC)
        return None
