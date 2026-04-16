from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ClinicalTrial(BaseModel):
    """Normalized ClinicalTrials.gov record."""

    nct_id: str
    title: str
    summary: str | None = None
    status: str
    conditions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    url: HttpUrl
    start_date: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Paper(BaseModel):
    """Normalized Semantic Scholar paper record."""

    paper_id: str
    title: str
    abstract: str | None = None
    doi: str | None = None
    external_ids: dict[str, str] = Field(default_factory=dict)
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    url: HttpUrl | None = None
    citation_count: int | None = None
