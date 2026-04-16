from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitonexus.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mitonexus.models.analysis_report import AnalysisReport


class AgentRun(Base, UUIDMixin, TimestampMixin):
    """Captured state for an agent execution tied to a report."""

    __tablename__ = "agent_runs"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_reports.id"))
    agent_name: Mapped[str] = mapped_column(String(255))
    state: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, nullable=False)
    tool_calls: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list, nullable=False)
    output: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(255))

    report: Mapped[AnalysisReport] = relationship(back_populates="agent_runs")
