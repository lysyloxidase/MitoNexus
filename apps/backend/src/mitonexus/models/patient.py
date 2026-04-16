from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitonexus.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mitonexus.models.analysis_report import AnalysisReport
    from mitonexus.models.blood_test import BloodTest


class Patient(Base, UUIDMixin, TimestampMixin):
    """Patient record linked to test results and reports."""

    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("age >= 18 AND age <= 120", name="patients_age_range"),
        CheckConstraint("sex IN ('M', 'F')", name="patients_sex_valid"),
    )

    age: Mapped[int]
    sex: Mapped[str] = mapped_column(String(1))
    test_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    blood_test: Mapped[BloodTest | None] = relationship(
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reports: Mapped[list[AnalysisReport]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )
