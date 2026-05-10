"""Model incydentu związanego z klientem lub jego wynajmem.

Pracownik może odnotować incydent (uszkodzenie pojazdu, opóźniony zwrot,
mandat, skarga) — ze stopniem ważności i powiązaniem z konkretnym
wynajmem, jeśli dotyczy. Severity wpływa na `risk_score` użytkownika
(logika w serwisie).
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rental import Rental
    from app.models.user import User


class IncidentSeverity(enum.StrEnum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class IncidentType(enum.StrEnum):
    DAMAGE = "damage"
    LATE_RETURN = "late_return"
    TRAFFIC_VIOLATION = "traffic_violation"
    COMPLAINT = "complaint"
    OTHER = "other"


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "cost IS NULL OR cost >= 0",
            name="ck_incident_cost_non_negative",
        ),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rental_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reported_by_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)

    type: Mapped[IncidentType] = mapped_column(Enum(IncidentType, native_enum=False), index=True)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, native_enum=False), index=True
    )
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    reported_by: Mapped[User] = relationship(foreign_keys=[reported_by_id])
    rental: Mapped[Rental | None] = relationship()
