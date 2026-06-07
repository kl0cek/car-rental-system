"""Modele rezerwacji, wynajmu i rozbicia ceny (dataclass, bez ORM).

`Reservation` to zamówienie klienta, `Rental` to faktyczne wydanie pojazdu
(powstaje gdy pracownik potwierdzi odbiór), a `RentalPriceBreakdown`
przechowuje składniki ostatecznej ceny (cena bazowa, mnożnik ryzyka).
Pola relacyjne (``vehicle``/``user``/``rental``/``reservation``/
``price_breakdown``) wypełnia repozytorium osobnymi zapytaniami.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.base import Entity
from app.models.user import User
from app.models.vehicle import Vehicle


class ReservationStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(kw_only=True)
class Reservation(Entity):
    user_id: uuid.UUID
    vehicle_id: uuid.UUID
    start_date: datetime
    end_date: datetime
    status: ReservationStatus = ReservationStatus.PENDING
    total_price: Decimal

    # Relacje dociągane przez repozytorium:
    vehicle: Vehicle | None = None
    user: User | None = None
    rental: Rental | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Reservation:
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            vehicle_id=row["vehicle_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=ReservationStatus(row["status"]),
            total_price=row["total_price"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(kw_only=True)
class Rental(Entity):
    reservation_id: uuid.UUID
    pickup_date: datetime
    mileage_start: int
    fuel_level_start: Decimal
    employee_id: uuid.UUID
    return_date: datetime | None = None
    mileage_end: int | None = None
    fuel_level_end: Decimal | None = None
    damage_notes: str | None = None

    # Relacje dociągane przez repozytorium:
    reservation: Reservation | None = None
    price_breakdown: RentalPriceBreakdown | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Rental:
        return cls(
            id=row["id"],
            reservation_id=row["reservation_id"],
            pickup_date=row["pickup_date"],
            return_date=row["return_date"],
            mileage_start=row["mileage_start"],
            mileage_end=row["mileage_end"],
            fuel_level_start=row["fuel_level_start"],
            fuel_level_end=row["fuel_level_end"],
            damage_notes=row["damage_notes"],
            employee_id=row["employee_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(kw_only=True)
class RentalPriceBreakdown(Entity):
    rental_id: uuid.UUID
    base_price: Decimal
    risk_multiplier: Decimal
    final_price: Decimal
    calculated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> RentalPriceBreakdown:
        return cls(
            id=row["id"],
            rental_id=row["rental_id"],
            base_price=row["base_price"],
            risk_multiplier=row["risk_multiplier"],
            final_price=row["final_price"],
            calculated_at=row["calculated_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
