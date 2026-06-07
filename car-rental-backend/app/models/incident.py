"""Model incydentu związanego z klientem lub jego wynajmem (dataclass).

Pracownik może odnotować incydent (uszkodzenie pojazdu, opóźniony zwrot,
mandat, skarga) — ze stopniem ważności i powiązaniem z konkretnym
wynajmem, jeśli dotyczy. Severity wpływa na `risk_score` użytkownika
(logika w serwisie). ``reported_by``/``customer`` dociąga repozytorium.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.db.base import Entity
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


@dataclass(kw_only=True)
class Incident(Entity):
    customer_id: uuid.UUID
    reported_by_id: uuid.UUID
    type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    rental_id: uuid.UUID | None = None
    cost: Decimal | None = None

    # Relacje dociągane przez repozytorium:
    customer: User | None = None
    reported_by: User | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Incident:
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            rental_id=row["rental_id"],
            reported_by_id=row["reported_by_id"],
            type=IncidentType(row["type"]),
            severity=IncidentSeverity(row["severity"]),
            title=row["title"],
            description=row["description"],
            cost=row["cost"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
