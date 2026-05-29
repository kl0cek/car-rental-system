"""Serwis rezerwacji.

Tworzenie rezerwacji z walidacją dostępności pojazdu, wyliczeniem
ceny (kategoria + risk_score), zmiana statusu (potwierdzenie /
anulowanie) i wysyłka maili powiadomień przy potwierdzeniu.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import date_to_utc_datetime
from app.models.rental import Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.models.vehicle import VehicleStatus
from app.repositories import reservation_repository, service_repository, vehicle_repository
from app.schemas.reservation import (
    CreateReservationRequest,
    ReservationConfirmedEmailData,
    ReservationListParams,
)


def _calculate_price(daily_base_price: Decimal, price_multiplier: Decimal, days: int) -> Decimal:
    return (daily_base_price * price_multiplier * days).quantize(Decimal("0.01"))


async def create_reservation(
    db: AsyncSession,
    current_user: User,
    body: CreateReservationRequest,
) -> Reservation:
    # SELECT ... FOR UPDATE — blokujemy wiersz pojazdu na czas transakcji,
    # żeby dwóch klientów nie zarezerwowało tego samego auta jednocześnie
    vehicle = await vehicle_repository.get_by_id_for_update(db, body.vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    # Operational lockout: a vehicle pulled off the floor by the service
    # team (or permanently retired) must not be bookable, even when the
    # date window is technically free.
    if vehicle.status in (VehicleStatus.MAINTENANCE, VehicleStatus.OUT_OF_SERVICE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vehicle is currently unavailable (status: {vehicle.status})",
        )

    # Even when the vehicle is still AVAILABLE/RENTED, a planned service
    # order may already exist for it. Block the reservation so the
    # technician's slot isn't double-booked.
    if await service_repository.has_active_service_for_vehicle(db, vehicle.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle has a pending service order — cannot be reserved",
        )

    conflicts = await vehicle_repository.count_conflicting_reservations(
        db, body.vehicle_id, body.start_date, body.end_date
    )
    if conflicts > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is not available for the selected dates",
        )

    days = (body.end_date - body.start_date).days
    total_price = _calculate_price(
        vehicle.daily_base_price, vehicle.category.price_multiplier, days
    )

    return await reservation_repository.create(
        db,
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        start_date=date_to_utc_datetime(body.start_date),
        end_date=date_to_utc_datetime(body.end_date),
        total_price=total_price,
    )


async def list_user_reservations(
    db: AsyncSession,
    current_user: User,
    params: ReservationListParams,
) -> tuple[list[Reservation], int]:
    return await reservation_repository.get_list_by_user(
        db,
        current_user.id,
        offset=params.offset,
        limit=params.limit,
        status=params.status,
    )


async def cancel_reservation(
    db: AsyncSession,
    current_user: User,
    reservation_id: uuid.UUID,
) -> Reservation:
    reservation = await reservation_repository.get_by_id(db, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    is_owner = reservation.user_id == current_user.id
    is_privileged = current_user.role in (UserRole.EMPLOYEE, UserRole.ADMIN)
    if not is_owner and not is_privileged:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if reservation.status not in (ReservationStatus.PENDING, ReservationStatus.CONFIRMED):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot cancel a reservation with status '{reservation.status}'",
        )

    # Reguła biznesowa: anulować można najpóźniej 24h przed rozpoczęciem rezerwacji
    now = datetime.now(tz=UTC)
    min_cancel_time = reservation.start_date - timedelta(hours=24)
    if now > min_cancel_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reservation can only be cancelled at least 24 hours before the start date",
        )

    return await reservation_repository.update_status(db, reservation, ReservationStatus.CANCELLED)


async def confirm_reservation(
    db: AsyncSession,
    reservation_id: uuid.UUID,
) -> tuple[Reservation, ReservationConfirmedEmailData]:
    reservation = await reservation_repository.get_by_id(db, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

    if reservation.status != ReservationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot confirm a reservation with status '{reservation.status}'",
        )

    reservation = await reservation_repository.update_status(
        db, reservation, ReservationStatus.CONFIRMED
    )

    user = reservation.user
    vehicle = reservation.vehicle
    email_data = ReservationConfirmedEmailData(
        to_email=user.email,
        first_name=user.first_name,
        vehicle_name=f"{vehicle.brand} {vehicle.model} ({vehicle.year})",
        start_date=reservation.start_date.date(),
        end_date=reservation.end_date.date(),
        total_price=reservation.total_price,
    )

    return reservation, email_data
