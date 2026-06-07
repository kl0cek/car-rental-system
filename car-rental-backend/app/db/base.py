"""Bazowy dataclass encji (zastępuje DeclarativeBase z SQLAlchemy).

Wszystkie modele dziedziczą wspólne kolumny ``id``, ``created_at``,
``updated_at``. ``id`` generowane jest po stronie aplikacji (UUID4), a
znaczniki czasu wypełnia baza (``DEFAULT now()``) i są dociągane przez
repozytoria klauzulą ``RETURNING``. Pola są ``kw_only``, dzięki czemu
podklasy mogą dodawać własne pola obowiązkowe bez konfliktu z domyślnymi
wartościami pól bazowych.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(kw_only=True)
class Entity:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
