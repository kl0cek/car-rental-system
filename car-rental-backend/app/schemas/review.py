"""Schematy DTO dla opinii o pojazdach.

Recenzje są przechowywane w kolekcji ``reviews`` w MongoDB (zgodnie z
założeniem projektu: dane niestrukturalne / komentarze trafiają do
dokumentów). Schemat poniżej waliduje payload przychodzący od klienta
oraz strukturę odpowiedzi z API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

MAX_COMMENT_LENGTH = 2000


class CreateReviewRequest(BaseModel):
    rental_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=MAX_COMMENT_LENGTH)


class ReviewAuthor(BaseModel):
    """Public author info embedded into review responses.

    Snapshotted into the Mongo document at write time so the public listing
    endpoint stays one round-trip (no per-review JOIN against Postgres users).
    If the underlying user changes their name/avatar, existing reviews keep
    the value from when they were written — a deliberate UX trade-off.
    """

    id: uuid.UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None


class ReviewResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    vehicle_id: uuid.UUID
    rental_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime
    author: ReviewAuthor


class PaginatedReviewResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    offset: int
    limit: int


class MyReviewedRentalsResponse(BaseModel):
    """List of rental IDs the current user has already reviewed.

    Lets the UI hide the "write review" button without re-fetching the full
    review documents.
    """

    rental_ids: list[uuid.UUID]
