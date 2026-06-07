"""Model użytkownika i wyliczenie ról (dataclass, bez ORM).

Obejmuje dane logowania, dane profilowe oraz `risk_score` używany przy
dynamicznym wyliczaniu ceny wynajmu na podstawie historii. ``from_row``
mapuje rekord asyncpg (tabela ``users``) na obiekt domenowy.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.base import Entity


class UserRole(enum.StrEnum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    TECHNICIAN = "technician"
    ADMIN = "admin"


@dataclass(kw_only=True)
class User(Entity):
    email: str
    hashed_password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    is_verified: bool = False
    phone: str | None = None
    avatar_url: str | None = None
    risk_score: Decimal = Decimal("0.00")
    last_login_at: datetime | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> User:
        return cls(
            id=row["id"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            role=UserRole(row["role"]),
            is_active=row["is_active"],
            is_verified=row["is_verified"],
            phone=row["phone"],
            avatar_url=row["avatar_url"],
            risk_score=row["risk_score"],
            last_login_at=row["last_login_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
