"""Model pojazdu wraz z wyliczeniami typu silnika, koloru i statusu (dataclass).

Unikalność VIN i tablicy rejestracyjnej jest wymuszana przez częściowy
indeks ``WHERE is_active = true`` (soft-delete nie blokuje ponownego
wprowadzenia). Pola ``category`` i ``images`` są dociągane przez
repozytorium (osobne zapytania) i wypełniane po zmapowaniu wiersza.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.db.base import Entity
from app.models.category import Category
from app.models.vehicle_image import VehicleImage


class EngineType(enum.StrEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class VehicleStatus(enum.StrEnum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class VehicleColor(enum.StrEnum):
    WHITE = "white"
    BLACK = "black"
    GREY = "grey"
    SILVER = "silver"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    BROWN = "brown"
    BEIGE = "beige"
    OTHER = "other"


@dataclass(kw_only=True)
class Vehicle(Entity):
    brand: str
    model: str
    year: int
    license_plate: str
    vin: str
    engine_type: EngineType
    horsepower: int
    seats: int
    trunk_capacity: int
    daily_base_price: Decimal
    color: VehicleColor
    category_id: uuid.UUID
    mileage: int = 0
    status: VehicleStatus = VehicleStatus.AVAILABLE
    is_active: bool = True
    avg_rating: Decimal | None = None
    ratings_count: int = 0

    # Relacje dociągane przez repozytorium (selectin-style):
    category: Category | None = None
    images: list[VehicleImage] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Vehicle:
        return cls(
            id=row["id"],
            brand=row["brand"],
            model=row["model"],
            year=row["year"],
            license_plate=row["license_plate"],
            vin=row["vin"],
            engine_type=EngineType(row["engine_type"]),
            horsepower=row["horsepower"],
            seats=row["seats"],
            trunk_capacity=row["trunk_capacity"],
            daily_base_price=row["daily_base_price"],
            color=VehicleColor(row["color"]),
            category_id=row["category_id"],
            mileage=row["mileage"],
            status=VehicleStatus(row["status"]),
            is_active=row["is_active"],
            avg_rating=row["avg_rating"],
            ratings_count=row["ratings_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
