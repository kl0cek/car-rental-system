"""Serwis wynajmu (pickup / return).

Pracownik potwierdza odbiór pojazdu (powstaje rekord `Rental` ze stanem
licznika i paliwa) oraz zwrot. Przy zwrocie wyliczana jest finalna cena
(z dopłatą paliwową) i zapisywana w `RentalPriceBreakdown`. Historia
trafia także do MongoDB.
"""

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
from app.repositories import rental_repository, reservation_repository, user_repository
from app.schemas.rental import PickupRequest, ReturnRequest
from app.schemas.user import UserRentalItem, UserRentalVehicleInfo


def _vehicle_primary_image_url(vehicle: Any) -> str | None:
    images = getattr(vehicle, "images", None) or []
    for img in images:
        if img.is_primary:
            return img.url
    if images:
        return min(images, key=lambda i: i.position).url
    return None


def compute_risk_multiplier(user_risk_score: Decimal | None) -> Decimal:
    """Map a user's risk score (0..100) to a rental price multiplier.

    Buckets are intentionally coarse to keep behavior predictable:

    * ``None`` or ``< 25`` → ``1.0000`` (no risk premium)
    * ``[25, 50)``        → ``1.0500`` (+5%)
    * ``[50, 75)``        → ``1.1500`` (+15%)
    * ``>= 75``           → ``1.3000`` (+30%)

    Called by both ``return_rental`` and the seed script — keep them aligned by
    importing this helper rather than copying thresholds.
    """
    if user_risk_score is None or user_risk_score < Decimal("25"):
        return Decimal("1.0000")
    if user_risk_score < Decimal("50"):
        return Decimal("1.0500")
    if user_risk_score < Decimal("75"):
        return Decimal("1.1500")
    return Decimal("1.3000")


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

    # Wyliczenie ceny finalnej:
    # - base_price: pierwotna cena z rezerwacji + dopłaty (np. szkody, czyszczenie)
    # - fuel_surcharge: dopłata za każdy "brakujący" % paliwa (tylko gdy auto wraca z mniejszym)
    # - risk_multiplier: pochodzi z risk_score klienta — mnoży końcową kwotę,
    #   żeby klienci z wyższym ryzykiem płacili więcej (patrz compute_risk_multiplier)
    reservation = rental.reservation
    base_price = (reservation.total_price + body.extra_charges).quantize(Decimal("0.01"))
    fuel_diff = rental.fuel_level_start - body.fuel_level_end
    fuel_surcharge = (
        max(fuel_diff, Decimal("0")) * settings.fuel_surcharge_rate_per_percent
    ).quantize(Decimal("0.01"))
    customer = await user_repository.get_by_id(db, reservation.user_id)
    risk_multiplier = compute_risk_multiplier(customer.risk_score if customer else None)
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
