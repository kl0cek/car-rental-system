"""Model zlecenia serwisowego pojazdu (dataclass, bez ORM).

Technik planuje i realizuje czynności serwisowe (przegląd, naprawa,
wymiana opon, mycie) na konkretnym pojeździe. Zlecenie ma cykl
``SCHEDULED → IN_PROGRESS → COMPLETED``. Pola ``vehicle``/``technician``/
``history_entries`` wypełnia repozytorium osobnymi zapytaniami.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.base import Entity
from app.models.service_history import ServiceHistory
from app.models.user import User
from app.models.vehicle import Vehicle


class ServiceType(enum.StrEnum):
    INSPECTION = "inspection"  # przegląd
    REPAIR = "repair"  # naprawa
    TIRE_SWAP = "tire_swap"  # wymiana_opon
    WASH = "wash"  # mycie


class ServiceOrderStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(kw_only=True)
class ServiceOrder(Entity):
    vehicle_id: uuid.UUID
    type: ServiceType
    description: str
    scheduled_date: datetime
    technician_id: uuid.UUID
    status: ServiceOrderStatus = ServiceOrderStatus.SCHEDULED
    cost: Decimal | None = None
    completed_date: datetime | None = None

    # Relacje dociągane przez repozytorium:
    vehicle: Vehicle | None = None
    technician: User | None = None
    history_entries: list[ServiceHistory] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> ServiceOrder:
        return cls(
            id=row["id"],
            vehicle_id=row["vehicle_id"],
            type=ServiceType(row["type"]),
            status=ServiceOrderStatus(row["status"]),
            description=row["description"],
            cost=row["cost"],
            scheduled_date=row["scheduled_date"],
            completed_date=row["completed_date"],
            technician_id=row["technician_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
