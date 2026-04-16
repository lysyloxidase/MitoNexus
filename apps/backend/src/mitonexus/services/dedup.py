from __future__ import annotations

import hashlib

from sqlalchemy import or_, select

from mitonexus.db.session import AsyncSessionLocal
from mitonexus.models import Publication


class DeduplicationService:
    """Three-tier publication deduplication."""

    def compute_content_hash(self, title: str, abstract: str | None, doi: str = "") -> str:
        """Hash normalized title, abstract, and DOI content."""
        abstract_text = abstract or ""
        payload = f"{title.strip().lower()}|{abstract_text.strip().lower()}|{doi.strip().lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def filter_new(self, source: str, external_ids: list[str]) -> list[str]:
        """Return only external ids that are not already stored for a source."""
        if not external_ids:
            return []

        async with AsyncSessionLocal() as session:
            result = await session.scalars(
                select(Publication.external_id).where(
                    Publication.source == source,
                    Publication.external_id.in_(external_ids),
                )
            )
            existing_ids = set(result.all())

        return [external_id for external_id in external_ids if external_id not in existing_ids]

    async def filter_publications(self, publications: list[Publication]) -> list[Publication]:
        """Drop publications already represented by source/external id, DOI, or content hash."""
        if not publications:
            return []

        for publication in publications:
            publication.content_hash = self.compute_content_hash(
                publication.title,
                publication.abstract,
                publication.doi or "",
            )

        external_ids = [publication.external_id for publication in publications]
        doi_values = [publication.doi for publication in publications if publication.doi]
        content_hashes = [publication.content_hash for publication in publications]

        async with AsyncSessionLocal() as session:
            filters = [Publication.external_id.in_(external_ids), Publication.content_hash.in_(content_hashes)]
            if doi_values:
                filters.append(Publication.doi.in_(doi_values))

            result = await session.execute(select(Publication).where(or_(*filters)))
            existing = result.scalars().all()

        existing_external_ids = {publication.external_id for publication in existing}
        existing_dois = {publication.doi for publication in existing if publication.doi}
        existing_hashes = {publication.content_hash for publication in existing}
        seen_external_ids: set[str] = set()
        seen_dois: set[str] = set()
        seen_hashes: set[str] = set()
        new_publications: list[Publication] = []

        for publication in publications:
            if publication.external_id in existing_external_ids or publication.external_id in seen_external_ids:
                continue
            if publication.content_hash in existing_hashes or publication.content_hash in seen_hashes:
                continue
            if publication.doi and (publication.doi in existing_dois or publication.doi in seen_dois):
                continue

            new_publications.append(publication)
            seen_external_ids.add(publication.external_id)
            seen_hashes.add(publication.content_hash)
            if publication.doi:
                seen_dois.add(publication.doi)

        return new_publications
