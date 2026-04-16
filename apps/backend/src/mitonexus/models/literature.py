from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mitonexus.models.base import Base, TimestampMixin, UUIDMixin


class Publication(Base, UUIDMixin, TimestampMixin):
    """Scientific literature metadata and embeddings."""

    __tablename__ = "publications"

    source: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mesh_terms: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    def to_summary_dict(self) -> dict[str, object]:
        """Return a lightweight literature summary payload."""
        abstract_excerpt = None
        if self.abstract:
            abstract_excerpt = (
                self.abstract[:317] + "..." if len(self.abstract) > 320 else self.abstract
            )

        return {
            "publication_id": str(self.id),
            "source": self.source,
            "external_id": self.external_id,
            "pmid": self.external_id if self.source == "pubmed" else None,
            "doi": self.doi,
            "title": self.title,
            "abstract_excerpt": abstract_excerpt,
            "publication_date": self.publication_date.isoformat()
            if self.publication_date
            else None,
            "authors": self.authors,
        }

    def to_detail_dict(self) -> dict[str, object]:
        """Return a richer evidence payload for reports and agents."""
        return {
            **self.to_summary_dict(),
            "abstract": self.abstract,
            "mesh_terms": self.mesh_terms,
        }
