from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle import Vehicle


class ReservationStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Reservation(Base):
    __tablename__ = "reservations"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vehicles.id"), index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, native_enum=False),
        default=ReservationStatus.PENDING,
        index=True,
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    user: Mapped[User] = relationship(back_populates="reservations")
    vehicle: Mapped[Vehicle] = relationship(back_populates="reservations")
    rental: Mapped[Rental | None] = relationship(back_populates="reservation", uselist=False)


class Rental(Base):
    __tablename__ = "rentals"
    __table_args__ = (
        CheckConstraint("mileage_start >= 0", name="ck_rental_mileage_start_non_negative"),
        CheckConstraint(
            "mileage_end IS NULL OR mileage_end >= mileage_start",
            name="ck_rental_mileage_end_gte_start",
        ),
        CheckConstraint(
            "fuel_level_start >= 0 AND fuel_level_start <= 100",
            name="ck_rental_fuel_level_start_range",
        ),
        CheckConstraint(
            "fuel_level_end IS NULL OR (fuel_level_end >= 0 AND fuel_level_end <= 100)",
            name="ck_rental_fuel_level_end_range",
        ),
        CheckConstraint(
            "return_date IS NULL OR return_date > pickup_date",
            name="ck_rental_return_after_pickup",
        ),
    )

    reservation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reservations.id"), unique=True
    )
    pickup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mileage_start: Mapped[int] = mapped_column(Integer)
    mileage_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_level_start: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    fuel_level_end: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    damage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)

    reservation: Mapped[Reservation] = relationship(back_populates="rental")
    employee: Mapped[User] = relationship(foreign_keys=[employee_id])
    price_breakdown: Mapped[RentalPriceBreakdown | None] = relationship(
        back_populates="rental", uselist=False
    )


class RentalPriceBreakdown(Base):
    __tablename__ = "rental_price_breakdowns"
    __table_args__ = (
        CheckConstraint("base_price >= 0", name="ck_price_breakdown_base_price_non_negative"),
        CheckConstraint(
            "fuel_surcharge >= 0", name="ck_price_breakdown_fuel_surcharge_non_negative"
        ),
        CheckConstraint(
            "risk_multiplier >= 1", name="ck_price_breakdown_risk_multiplier_gte_one"
        ),
        CheckConstraint("final_price >= 0", name="ck_price_breakdown_final_price_non_negative"),
    )

    rental_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rentals.id"), unique=True
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fuel_surcharge: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    risk_multiplier: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    final_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    rental: Mapped[Rental] = relationship(back_populates="price_breakdown")
