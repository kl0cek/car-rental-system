"""Model kategorii pojazdu (dataclass, bez ORM).

`price_multiplier` to mnożnik bazowej ceny dziennej pojazdu zależny od
kategorii (ekonomiczna, komfort, premium, SUV, van).
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.db.base import Entity


class CategoryName(enum.StrEnum):
    ECONOMY = "economy"
    COMFORT = "comfort"
    PREMIUM = "premium"
    SUV = "suv"
    VAN = "van"


@dataclass(kw_only=True)
class Category(Entity):
    name: CategoryName
    description: str | None = None
    price_multiplier: Decimal = Decimal("1.000")

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Category:
        return cls(
            id=row["id"],
            name=CategoryName(row["name"]),
            description=row["description"],
            price_multiplier=row["price_multiplier"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
