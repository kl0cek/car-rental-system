from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.rental import Rental


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


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("horsepower > 0", name="ck_vehicle_horsepower_positive"),
        CheckConstraint("seats > 0", name="ck_vehicle_seats_positive"),
        CheckConstraint("trunk_capacity >= 0", name="ck_vehicle_trunk_capacity_non_negative"),
        CheckConstraint("mileage >= 0", name="ck_vehicle_mileage_non_negative"),
    )

    brand: Mapped[str] = mapped_column(String(100), index=True)
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    license_plate: Mapped[str] = mapped_column(String(20), unique=True)
    vin: Mapped[str] = mapped_column(String(17), unique=True)
    engine_type: Mapped[EngineType] = mapped_column(Enum(EngineType, native_enum=False), index=True)
    horsepower: Mapped[int] = mapped_column(Integer)
    seats: Mapped[int] = mapped_column(Integer)
    trunk_capacity: Mapped[int] = mapped_column(Integer)
    daily_base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    color: Mapped[str] = mapped_column(String(50))
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, native_enum=False), default=VehicleStatus.AVAILABLE, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("categories.id"), index=True)

    category: Mapped[Category] = relationship(back_populates="vehicles")
    rentals: Mapped[list[Rental]] = relationship(back_populates="vehicle")
