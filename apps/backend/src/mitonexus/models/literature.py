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
