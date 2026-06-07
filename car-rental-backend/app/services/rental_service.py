"""Serwis wynajmu (pickup / return).

Pracownik potwierdza odbiór pojazdu (powstaje rekord `Rental` ze stanem
licznika i poziomu paliwa) oraz zwrot. Przy zwrocie wyliczana jest finalna
cena (`base * risk * dni`, gdzie kategoria pojazdu wpływa już na `base`)
i zapisywana w `RentalPriceBreakdown`. Historia trafia także do MongoDB.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.redis import get_redis
from app.db.session import Db
from app.models.rental import Rental, ReservationStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories import rental_repository, reservation_repository, user_repository
from app.schemas.rental import PickupRequest, ReturnRequest
from app.schemas.user import UserRentalItem, UserRentalVehicleInfo
from app.services import risk_scoring


def _vehicle_primary_image_url(vehicle: Vehicle) -> str | None:
    images = list(vehicle.images or [])
    for img in images:
        if img.is_primary:
            return img.url
    if images:
        return min(images, key=lambda i: i.position).url
    return None


def compute_risk_multiplier(user_risk_score: Decimal | None) -> Decimal:
    """Map a user's risk score (0..100) to a rental price multiplier in [0.8, 1.5].

    Piecewise mapping designed so that customers with a clean history get a
    discount, while higher-risk customers pay a premium:

    * ``None``        → ``1.0000`` (neutral baseline for users without a score)
    * ``< 20``        → ``0.8000`` (-20% loyalty/clean-history discount)
    * ``[20, 40)``    → ``0.9000`` (-10%)
    * ``[40, 60)``    → ``1.0000`` (neutral)
    * ``[60, 80)``    → ``1.2000`` (+20%)
    * ``>= 80``       → ``1.5000`` (+50%)

    Called by both ``return_rental`` and the seed script — keep them aligned by
    importing this helper rather than copying thresholds.
    """
    if user_risk_score is None:
        return Decimal("1.0000")
    if user_risk_score < Decimal("20"):
        return Decimal("0.8000")
    if user_risk_score < Decimal("40"):
        return Decimal("0.9000")
    if user_risk_score < Decimal("60"):
        return Decimal("1.0000")
    if user_risk_score < Decimal("80"):
        return Decimal("1.2000")
    return Decimal("1.5000")


def build_user_rental_item(rental: Rental) -> UserRentalItem:
    reservation = rental.reservation
    vehicle = reservation.vehicle
    return UserRentalItem(
        id=rental.id,
        reservation_id=rental.reservation_id,
        vehicle=UserRentalVehicleInfo(
            id=vehicle.id,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year,
            license_plate=vehicle.license_plate,
            image_url=_vehicle_primary_image_url(vehicle),
        ),
        pickup_date=rental.pickup_date,
        return_date=rental.return_date,
        status=reservation.status,
        total_price=reservation.total_price,
        final_price=rental.price_breakdown.final_price if rental.price_breakdown else None,
        created_at=rental.created_at,
    )


async def pickup_rental(
    db: Db,
    current_user: User,
    reservation_id: uuid.UUID,
    body: PickupRequest,
) -> Rental:
    reservation = await reservation_repository.get_by_id_for_update(db, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if reservation.status != ReservationStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot process pickup for a reservation with status '{reservation.status}'",
        )

    existing = await rental_repository.get_by_reservation_id(db, reservation_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rental already exists for this reservation",
        )

    rental = await rental_repository.create_pickup(
        db,
        reservation_id=reservation_id,
        employee_id=current_user.id,
        mileage_start=body.mileage_start,
        fuel_level_start=body.fuel_level_start,
        pickup_date=datetime.now(tz=UTC),
    )

    await reservation_repository.update_status(db, reservation, ReservationStatus.ACTIVE)

    return rental


async def return_rental(
    db: Db,
    current_user: User,
    rental_id: uuid.UUID,
    body: ReturnRequest,
) -> Rental:
    rental = await rental_repository.get_by_id(db, rental_id)
    if rental is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")

    if rental.return_date is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rental has already been returned",
        )

    if body.mileage_end < rental.mileage_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mileage_end must be greater than or equal to mileage_start",
        )

    rental = await rental_repository.update_return(
        db,
        rental,
        mileage_end=body.mileage_end,
        fuel_level_end=body.fuel_level_end,
        damage_notes=body.damage_notes,
        return_date=datetime.now(tz=UTC),
    )

    # Wyliczenie ceny finalnej:
    # - base_price: pierwotna cena z rezerwacji (daily_base * category_mult * dni)
    #   + ewentualne dopłaty pracownicze (szkody, czyszczenie)
    # - risk_multiplier: pochodzi z risk_score klienta — mnoży końcową kwotę,
    #   żeby klienci z wyższym ryzykiem płacili więcej (patrz compute_risk_multiplier)
    reservation = rental.reservation
    base_price = (reservation.total_price + body.extra_charges).quantize(Decimal("0.01"))
    customer = await user_repository.get_by_id(db, reservation.user_id)
    risk_multiplier = compute_risk_multiplier(customer.risk_score if customer else None)
    final_price = (base_price * risk_multiplier).quantize(Decimal("0.01"))

    breakdown = await rental_repository.create_price_breakdown(
        db,
        rental_id=rental.id,
        base_price=base_price,
        risk_multiplier=risk_multiplier,
        final_price=final_price,
    )
    rental.price_breakdown = breakdown

    await reservation_repository.update_status(db, reservation, ReservationStatus.COMPLETED)

    # Event-driven update: recompute risk_score from the user's full history so the
    # next rental's multiplier reflects this return (and any incidents reported on it).
    # Pass redis so the cached User record gets invalidated alongside the DB write —
    # otherwise the next price quote in this session would still see the old score.
    await risk_scoring.recompute_and_persist(db, reservation.user_id, get_redis())

    return rental


async def log_pickup(
    mongo: AsyncIOMotorDatabase[Any],
    rental_id: uuid.UUID,
    reservation_id: uuid.UUID,
    employee_id: uuid.UUID,
    photo_urls: list[str],
    client_signature_url: str | None,
) -> None:
    await mongo["rental_logs"].insert_one(
        {
            "rental_id": str(rental_id),
            "reservation_id": str(reservation_id),
            "event": "pickup",
            "employee_id": str(employee_id),
            "photo_urls": photo_urls,
            "client_signature_url": client_signature_url,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
    )


async def log_return(
    mongo: AsyncIOMotorDatabase[Any],
    rental_id: uuid.UUID,
    reservation_id: uuid.UUID,
    employee_id: uuid.UUID,
    damage_photo_urls: list[str],
) -> None:
    await mongo["rental_logs"].insert_one(
        {
            "rental_id": str(rental_id),
            "reservation_id": str(reservation_id),
            "event": "return",
            "employee_id": str(employee_id),
            "damage_photo_urls": damage_photo_urls,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }
    )
