from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rental import Reservation


class UserRole(enum.StrEnum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_user_risk_score_range",
        ),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(Text)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.CUSTOMER, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    reservations: Mapped[list[Reservation]] = relationship(back_populates="user")
