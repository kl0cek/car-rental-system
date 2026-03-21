from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
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

    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    license_plate: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    engine_type: Mapped[EngineType] = mapped_column(String(20))
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    seats: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(String(50))
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(String(20), default=VehicleStatus.AVAILABLE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    rentals: Mapped[list["Rental"]] = relationship(back_populates="vehicle")  # noqa: F821
