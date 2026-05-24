"""Model wpisu w historii serwisowej pojazdu.

Każdy wpis dokumentuje wykonaną czynność serwisową — notatki technika,
listę wymienionych części oraz przebieg pojazdu w momencie serwisu.
Powiązany 1:N z konkretnym ``ServiceOrder``; przy usunięciu zlecenia
historia również jest usuwana (cascade).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ``parts_replaced`` is a list of free-text part identifiers. On PostgreSQL
# (production) it is a native ``TEXT[]`` — queryable with array operators
# and indexable with GIN if we ever need to filter by part. On SQLite
# (test only) we fall back to JSON, since SQLite has no array type.
# ``with_variant`` keeps the production schema unchanged while letting the
# aiosqlite-backed test fixture create the table at all.
_PartsReplacedType = ARRAY(Text()).with_variant(JSON(), "sqlite")

if TYPE_CHECKING:
    from app.models.service_order import ServiceOrder
    from app.models.vehicle import Vehicle


class ServiceHistory(Base):
    __tablename__ = "service_history"
    __table_args__ = (
        CheckConstraint(
            "mileage_at_service >= 0",
            name="ck_service_history_mileage_non_negative",
        ),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    service_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("service_orders.id", ondelete="CASCADE"), index=True
    )
    notes: Mapped[str] = mapped_column(Text)
    parts_replaced: Mapped[list[str]] = mapped_column(
        _PartsReplacedType, nullable=False, server_default="{}"
    )
    mileage_at_service: Mapped[int] = mapped_column(Integer)

    vehicle: Mapped[Vehicle] = relationship()
    service_order: Mapped[ServiceOrder] = relationship(back_populates="history_entries")
