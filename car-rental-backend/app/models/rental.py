from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle import Vehicle


class RentalStatus(enum.StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Rental(Base):
    __tablename__ = "rentals"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vehicles.id"), index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[RentalStatus] = mapped_column(Enum(RentalStatus, native_enum=False), default=RentalStatus.PENDING)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="rentals")
    vehicle: Mapped[Vehicle] = relationship(back_populates="rentals")
