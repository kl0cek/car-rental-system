"""Notatki pracownika o kliencie.

Wewnętrzne adnotacje widoczne tylko dla staffu — np. ustalenia
telefoniczne, preferencje klienta, ostrzeżenia. Niewidoczne dla
samego klienta w jego panelu.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class CustomerNote(Base):
    __tablename__ = "customer_notes"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    author: Mapped[User] = relationship(foreign_keys=[author_id])
