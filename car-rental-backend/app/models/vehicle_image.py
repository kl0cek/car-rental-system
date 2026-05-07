"""Model zdjęcia pojazdu (1:N).

Każdy pojazd może mieć wiele zdjęć z określoną kolejnością wyświetlania
(`position`) i dokładnie jednym zdjęciem oznaczonym jako podstawowe
(`is_primary` — wymuszane częściowym indeksem unikatowym).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class VehicleImage(Base):
    __tablename__ = "vehicle_images"
    __table_args__ = (
        Index(
            "uq_vehicle_images_one_primary_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
        Index("ix_vehicle_images_vehicle_id_position", "vehicle_id", "position"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="images")
