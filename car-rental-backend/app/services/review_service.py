"""Serwis recenzji pojazdów.

Reguły biznesowe:

* Recenzję może wystawić tylko klient, który faktycznie zakończył dany
  wynajem (rezerwacja w statusie ``COMPLETED``).
* Każdy klient może wystawić co najwyżej jedną recenzję per wynajem —
  wymuszane przez unikalny indeks compound w MongoDB na
  ``(rental_id, user_id)``.
* Po dodaniu / usunięciu opinii przeliczamy ``avg_rating`` i
  ``ratings_count`` na rekordzie pojazdu w Postgresie — pełni to rolę
  triggera, ale jest sterowane z aplikacji, ponieważ źródłem prawdy dla
  recenzji jest Mongo, a wartości agregowane chcemy mieć w katalogu
  (Postgres) bez ciągłej agregacji po stronie odczytu.
"""

import uuid
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.rental import Rental, Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.repositories import review_repository
from app.schemas.review import (
    CreateReviewRequest,
    MyReviewedRentalsResponse,
    PaginatedReviewResponse,
    ReviewAuthor,
    ReviewResponse,
)


def _author_from_doc(doc: dict[str, Any]) -> ReviewAuthor:
    # Legacy docs (pre-author migration) won't have the embedded author —
    # synthesise a minimal one from user_id so listing endpoints don't crash.
    author = doc.get("author") or {}
    return ReviewAuthor(
        id=uuid.UUID(author.get("id") or doc["user_id"]),
        first_name=author.get("first_name") or "",
        last_name=author.get("last_name") or "",
        avatar_url=author.get("avatar_url"),
    )


def _to_response(doc: dict[str, Any]) -> ReviewResponse:
    return ReviewResponse(
        id=uuid.UUID(doc["_id"]),
        user_id=uuid.UUID(doc["user_id"]),
        vehicle_id=uuid.UUID(doc["vehicle_id"]),
        rental_id=uuid.UUID(doc["rental_id"]),
        rating=int(doc["rating"]),
        comment=doc.get("comment"),
        created_at=doc["created_at"],
        author=_author_from_doc(doc),
    )


async def _refresh_vehicle_rating(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase[Any],
    vehicle_id: uuid.UUID,
) -> None:
    """Recompute aggregates from Mongo and persist them on the vehicle row.

    Called after each insert / delete. Recomputing from the source of truth
    avoids drift from delta-based bookkeeping. The vehicle row is locked with
    ``SELECT ... FOR UPDATE`` first so concurrent writers serialize per
    vehicle — without it two parallel inserts could each read Mongo and then
    overwrite the other's ``UPDATE`` with a stale aggregate (lost update).

    Note: this only protects the Postgres-side aggregate. If the Mongo write
    succeeded but the surrounding request transaction later rolls back, the
    aggregate will be briefly stale until the next review event triggers
    another refresh. Acceptable for a denormalised view; a periodic
    reconciliation job is the planned long-term safety net.
    """
    # Lock the vehicle row for the rest of this transaction. Reads of the
    # source of truth (Mongo) happen *after* the lock is held, so any
    # concurrent writer has either committed its Mongo insert before we
    # aggregated (we'll see it) or is queued behind our lock (it'll re-read
    # the post-our-commit state).
    await db.execute(
        select(Vehicle.id).where(Vehicle.id == vehicle_id).with_for_update()
    )
    avg, count = await review_repository.aggregate_rating(mongo, vehicle_id)
    avg_decimal = None if avg is None else Decimal(str(avg))
    await db.execute(
        update(Vehicle)
        .where(Vehicle.id == vehicle_id)
        .values(avg_rating=avg_decimal, ratings_count=count)
    )


async def _load_rental_for_review(
    db: AsyncSession, rental_id: uuid.UUID
) -> tuple[Rental, Reservation]:
    """Fetch the rental with its reservation eager-loaded, or 404."""
    stmt = (
        select(Rental)
        .options(joinedload(Rental.reservation))
        .where(Rental.id == rental_id)
    )
    result = await db.execute(stmt)
    rental = result.scalar_one_or_none()
    if rental is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found"
        )
    return rental, rental.reservation


async def create_review(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase[Any],
    current_user: User,
    body: CreateReviewRequest,
) -> ReviewResponse:
    rental, reservation = await _load_rental_for_review(db, body.rental_id)

    if reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review your own rentals",
        )
    if reservation.status != ReservationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="You can only review a completed rental",
        )

    try:
        doc = await review_repository.insert(
            mongo,
            user_id=current_user.id,
            vehicle_id=reservation.vehicle_id,
            rental_id=rental.id,
            rating=body.rating,
            comment=body.comment,
            author_first_name=current_user.first_name,
            author_last_name=current_user.last_name,
            author_avatar_url=current_user.avatar_url,
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review already exists for this rental",
        )

    await _refresh_vehicle_rating(db, mongo, reservation.vehicle_id)
    return _to_response(doc)


async def list_vehicle_reviews(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase[Any],
    vehicle_id: uuid.UUID,
    *,
    offset: int,
    limit: int,
) -> PaginatedReviewResponse:
    # 404 on unknown vehicle so the contract matches GET /vehicles/{id};
    # otherwise typos silently return an empty page.
    exists = await db.scalar(
        select(Vehicle.id).where(Vehicle.id == vehicle_id, Vehicle.is_active.is_(True))
    )
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
        )

    items, total = await review_repository.list_for_vehicle(
        mongo, vehicle_id, offset=offset, limit=limit
    )
    return PaginatedReviewResponse(
        items=[_to_response(d) for d in items],
        total=total,
        offset=offset,
        limit=limit,
    )


async def list_my_reviewed_rental_ids(
    mongo: AsyncIOMotorDatabase[Any], current_user: User
) -> MyReviewedRentalsResponse:
    raw_ids = await review_repository.list_user_rental_ids(mongo, current_user.id)
    return MyReviewedRentalsResponse(rental_ids=[uuid.UUID(i) for i in raw_ids])


async def list_all_reviews(
    mongo: AsyncIOMotorDatabase[Any],
    *,
    offset: int,
    limit: int,
) -> PaginatedReviewResponse:
    """Admin-only flat listing across all vehicles, newest first."""
    items, total = await review_repository.list_all(mongo, offset=offset, limit=limit)
    return PaginatedReviewResponse(
        items=[_to_response(d) for d in items],
        total=total,
        offset=offset,
        limit=limit,
    )


async def delete_review(
    db: AsyncSession,
    mongo: AsyncIOMotorDatabase[Any],
    current_user: User,
    review_id: uuid.UUID,
) -> None:
    if current_user.role != UserRole.ADMIN:
        # Defense in depth — the router also enforces the role via Depends.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    doc = await review_repository.find_and_delete_by_id(mongo, review_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    await _refresh_vehicle_rating(db, mongo, uuid.UUID(doc["vehicle_id"]))
