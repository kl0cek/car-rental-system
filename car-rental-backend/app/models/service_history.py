"""Model wpisu w historii serwisowej pojazdu (dataclass, bez ORM).

Każdy wpis dokumentuje wykonaną czynność serwisową — notatki technika,
listę wymienionych części (``parts_replaced`` → kolumna ``TEXT[]``) oraz
przebieg pojazdu w momencie serwisu. Powiązany 1:N z ``ServiceOrder``.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.db.base import Entity


@dataclass(kw_only=True)
class ServiceHistory(Entity):
    vehicle_id: uuid.UUID
    service_order_id: uuid.UUID
    notes: str
    mileage_at_service: int
    parts_replaced: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> ServiceHistory:
        return cls(
            id=row["id"],
            vehicle_id=row["vehicle_id"],
            service_order_id=row["service_order_id"],
            notes=row["notes"],
            parts_replaced=list(row["parts_replaced"] or []),
            mileage_at_service=row["mileage_at_service"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
