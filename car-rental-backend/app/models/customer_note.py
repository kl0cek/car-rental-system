"""Notatki pracownika o kliencie (dataclass, bez ORM).

Wewnętrzne adnotacje widoczne tylko dla staffu — np. ustalenia
telefoniczne, preferencje klienta, ostrzeżenia. ``author`` (autor notatki)
dociąga repozytorium osobnym zapytaniem.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.db.base import Entity
from app.models.user import User


@dataclass(kw_only=True)
class CustomerNote(Entity):
    customer_id: uuid.UUID
    author_id: uuid.UUID
    body: str

    # Relacja dociągana przez repozytorium:
    author: User | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> CustomerNote:
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            author_id=row["author_id"],
            body=row["body"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
