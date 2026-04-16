from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mitonexus.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mitonexus.models.patient import Patient


class BloodTest(Base, UUIDMixin, TimestampMixin):
    """Raw and derived blood-test values for a patient."""

    __tablename__ = "blood_tests"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), unique=True)
    raw_values: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)
    derived_values: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="blood_test")
