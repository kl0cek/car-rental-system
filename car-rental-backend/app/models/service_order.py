"""Model zlecenia serwisowego pojazdu.

Technik planuje i realizuje czynności serwisowe (przegląd, naprawa,
wymiana opon, mycie) na konkretnym pojeździe. Zlecenie ma cykl
``SCHEDULED → IN_PROGRESS → COMPLETED``. Po zakończeniu mogą powstać
wpisy w ``service_history`` z listą wymienionych części i przebiegiem
w momencie wykonania.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.service_history import ServiceHistory
    from app.models.user import User
    from app.models.vehicle import Vehicle


class ServiceType(enum.StrEnum):
    INSPECTION = "inspection"  # przegląd
    REPAIR = "repair"  # naprawa
    TIRE_SWAP = "tire_swap"  # wymiana_opon
    WASH = "wash"  # mycie


class ServiceOrderStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ServiceOrder(Base):
    __tablename__ = "service_orders"
    __table_args__ = (
        CheckConstraint(
            "cost IS NULL OR cost >= 0",
            name="ck_service_order_cost_non_negative",
        ),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[ServiceType] = mapped_column(Enum(ServiceType, native_enum=False), index=True)
    status: Mapped[ServiceOrderStatus] = mapped_column(
        Enum(ServiceOrderStatus, native_enum=False),
        default=ServiceOrderStatus.SCHEDULED,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    technician_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", name="fk_service_orders_technician_id"),
        index=True,
    )

    vehicle: Mapped[Vehicle] = relationship()
    technician: Mapped[User] = relationship()
    history_entries: Mapped[list[ServiceHistory]] = relationship(
        back_populates="service_order", cascade="all, delete-orphan"
    )
