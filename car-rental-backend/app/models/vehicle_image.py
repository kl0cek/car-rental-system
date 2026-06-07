"""Model zdjęcia pojazdu (dataclass, bez ORM).

Każdy pojazd może mieć wiele zdjęć z określoną kolejnością wyświetlania
(`position`) i dokładnie jednym zdjęciem podstawowym (`is_primary` —
wymuszane częściowym indeksem unikatowym ``WHERE is_primary = true``).
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.db.base import Entity


@dataclass(kw_only=True)
class VehicleImage(Entity):
    vehicle_id: uuid.UUID
    url: str
    position: int = 0
    is_primary: bool = False

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> VehicleImage:
        return cls(
            id=row["id"],
            vehicle_id=row["vehicle_id"],
            url=row["url"],
            position=row["position"],
            is_primary=row["is_primary"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
