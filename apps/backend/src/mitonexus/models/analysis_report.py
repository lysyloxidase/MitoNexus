from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitonexus.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mitonexus.models.agent_run import AgentRun
    from mitonexus.models.patient import Patient


class AnalysisReport(Base, UUIDMixin, TimestampMixin):
    """Generated report for a patient analysis run."""

    __tablename__ = "analysis_reports"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"))
    mitoscore: Mapped[float | None] = mapped_column(Float)
    mitoscore_components: Mapped[dict[str, float] | None] = mapped_column(JSONB)
    affected_cascades: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    therapy_plan: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    pdf_path: Mapped[str | None]
    visualization_data: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    patient: Mapped[Patient] = relationship(back_populates="reports")
    agent_runs: Mapped[list[AgentRun]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )
