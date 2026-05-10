"""Model pojazdu wraz z wyliczeniami typu silnika i statusu.

Unikalność VIN i tablicy rejestracyjnej jest wymuszana przez częściowy
indeks `WHERE is_active = true` — soft-delete nie blokuje ponownego
wprowadzenia tego samego pojazdu fizycznego.
"""

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.rental import Reservation
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


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("horsepower > 0", name="ck_vehicle_horsepower_positive"),
        CheckConstraint("seats > 0", name="ck_vehicle_seats_positive"),
        CheckConstraint("trunk_capacity >= 0", name="ck_vehicle_trunk_capacity_non_negative"),
        CheckConstraint("mileage >= 0", name="ck_vehicle_mileage_non_negative"),
        Index(
            "uq_vehicles_vin_active",
            "vin",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "uq_vehicles_license_plate_active",
            "license_plate",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    brand: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    license_plate: Mapped[str] = mapped_column(String(20))
    vin: Mapped[str] = mapped_column(String(17))
    engine_type: Mapped[EngineType] = mapped_column(Enum(EngineType, native_enum=False), index=True)
    horsepower: Mapped[int] = mapped_column(Integer)
    seats: Mapped[int] = mapped_column(Integer)
    trunk_capacity: Mapped[int] = mapped_column(Integer)
    daily_base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    color: Mapped[VehicleColor] = mapped_column(Enum(VehicleColor, native_enum=False), index=True)
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, native_enum=False), default=VehicleStatus.AVAILABLE, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("categories.id"), index=True)

    category: Mapped[Category] = relationship(back_populates="vehicles")
    reservations: Mapped[list[Reservation]] = relationship(back_populates="vehicle")
    images: Mapped[list[VehicleImage]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="VehicleImage.position",
    )
