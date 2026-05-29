"""Router opinii o pojazdach (`/reviews`).

* ``POST /reviews``         — klient dodaje opinię po zakończonym wynajmie.
* ``DELETE /reviews/{id}``  — admin usuwa pojedynczą opinię (moderacja).

Listing opinii dla pojazdu znajduje się w routerze ``vehicles`` —
``GET /vehicles/{id}/reviews`` — żeby pasować do hierarchii zasobów
i konwencji REST.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import CurrentUser, require_roles
from app.db.mongodb import get_mongo_db
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.review import (
    CreateReviewRequest,
    MyReviewedRentalsResponse,
    PaginatedReviewResponse,
    ReviewResponse,
)
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["reviews"])

AdminOnly = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
MongoDep = Annotated[AsyncIOMotorDatabase[Any], Depends(get_mongo_db)]


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: CreateReviewRequest,
    db: DbSession,
    mongo: MongoDep,
    current_user: CurrentUser,
) -> ReviewResponse:
    return await review_service.create_review(db, mongo, current_user, body)


@router.get("/me/rentals", response_model=MyReviewedRentalsResponse)
async def list_my_reviewed_rentals(
    mongo: MongoDep,
    current_user: CurrentUser,
) -> MyReviewedRentalsResponse:
    """Rental IDs the current user already reviewed.

    Used by the bookings table to hide the "write review" button on rentals
    that already have a review, so the user doesn't get a 409 by clicking it.
    """
    return await review_service.list_my_reviewed_rental_ids(mongo, current_user)


@router.get("", response_model=PaginatedReviewResponse)
async def list_all_reviews(
    mongo: MongoDep,
    _admin: AdminOnly,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedReviewResponse:
    """Admin-only flat listing across all vehicles — feeds the moderation page."""
    return await review_service.list_all_reviews(mongo, offset=offset, limit=limit)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: Annotated[uuid.UUID, Path()],
    db: DbSession,
    mongo: MongoDep,
    current_user: AdminOnly,
) -> None:
    await review_service.delete_review(db, mongo, current_user, review_id)
