import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.rental import Rental, ReservationStatus
from app.models.user import User
from app.repositories import rental_repository, reservation_repository
from app.schemas.rental import PickupRequest, ReturnRequest


async def pickup_rental(
    db: AsyncSession,
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
    db: AsyncSession,
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

    reservation = rental.reservation
    base_price = (reservation.total_price + body.extra_charges).quantize(Decimal("0.01"))
    fuel_diff = rental.fuel_level_start - body.fuel_level_end
    fuel_surcharge = (
        max(fuel_diff, Decimal("0")) * settings.fuel_surcharge_rate_per_percent
    ).quantize(Decimal("0.01"))
    risk_multiplier = Decimal("1.0000")
    final_price = ((base_price + fuel_surcharge) * risk_multiplier).quantize(Decimal("0.01"))

    breakdown = await rental_repository.create_price_breakdown(
        db,
        rental_id=rental.id,
        base_price=base_price,
        fuel_surcharge=fuel_surcharge,
        risk_multiplier=risk_multiplier,
        final_price=final_price,
    )
    rental.price_breakdown = breakdown

    await reservation_repository.update_status(db, reservation, ReservationStatus.COMPLETED)

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
