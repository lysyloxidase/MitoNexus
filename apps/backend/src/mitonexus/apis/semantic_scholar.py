from __future__ import annotations

from typing import Any

from mitonexus.apis.base import BaseAPIClient
from mitonexus.config import get_settings
from mitonexus.schemas import Paper


class SemanticScholarClient(BaseAPIClient):
    """Semantic Scholar Graph API client."""

    base_url = "https://api.semanticscholar.org/graph/v1"
    rate_limit_per_second = 16.0

    def __init__(self) -> None:
        super().__init__()
        self._api_key = get_settings().semantic_scholar_key

    async def search_papers(self, query: str, fields: list[str]) -> list[Paper]:
        """Search Semantic Scholar papers with a configurable field set."""
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        response = await self._request(
            "GET",
            "/paper/search",
            params={
                "query": query,
                "fields": ",".join(fields),
                "limit": 100,
            },
            headers=headers,
        )
        payload = response.json()
        papers = payload.get("data", [])
        return [paper for paper in (self._parse_paper(item) for item in papers) if paper is not None]

    def _parse_paper(self, item: dict[object, object]) -> Paper | None:
        paper_id = item.get("paperId")
        title = item.get("title")
        if not isinstance(paper_id, str) or not isinstance(title, str):
            return None

        external_ids = item.get("externalIds", {})
        normalized_external_ids: dict[str, str] = {}
        if isinstance(external_ids, dict):
            normalized_external_ids = {
                str(key): str(value)
                for key, value in external_ids.items()
                if isinstance(value, str) and value
            }

        authors = item.get("authors", [])
        author_names: list[str] = []
        if isinstance(authors, list):
            author_names = [
                str(author["name"])
                for author in authors
                if isinstance(author, dict) and isinstance(author.get("name"), str)
            ]

        url = item.get("url")
        normalized_url = str(url) if isinstance(url, str) and url else None

        return Paper(
            paper_id=paper_id,
            title=title,
            abstract=self._normalize_text(item.get("abstract")),
            doi=normalized_external_ids.get("DOI"),
            external_ids=normalized_external_ids,
            authors=author_names,
            year=self._coerce_int(item.get("year")),
            venue=self._normalize_text(item.get("venue")),
            url=normalized_url,
            citation_count=self._coerce_int(item.get("citationCount")),
        )

    def _normalize_text(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _coerce_int(self, value: Any) -> int | None:
        return value if isinstance(value, int) else None
