from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class CategoryName(enum.StrEnum):
    ECONOMY = "economy"
    COMFORT = "comfort"
    PREMIUM = "premium"
    SUV = "suv"
    VAN = "van"


class Category(Base):
    __tablename__ = "categories"

    name: Mapped[CategoryName] = mapped_column(String(20), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.00"))

    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="category")
