import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental import Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.repositories import reservation_repository, vehicle_repository
from app.schemas.reservation import (
    CreateReservationRequest,
    PaginatedReservationResponse,
    ReservationListParams,
    ReservationResponse,
)


@dataclass
class ReservationConfirmedEmailData:
    to_email: str
    first_name: str
    vehicle_name: str
    start_date: date
    end_date: date
    total_price: Decimal


def _date_to_datetime(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=UTC)


def _calculate_price(daily_base_price: Decimal, price_multiplier: Decimal, days: int) -> Decimal:
    return (daily_base_price * price_multiplier * days).quantize(Decimal("0.01"))


async def create_reservation(
    db: AsyncSession,
    current_user: User,
    body: CreateReservationRequest,
) -> Reservation:
    vehicle = await vehicle_repository.get_by_id(db, body.vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

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

    reservation = await reservation_repository.create(
        db,
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        start_date=_date_to_datetime(body.start_date),
        end_date=_date_to_datetime(body.end_date),
        total_price=total_price,
    )
    return reservation


async def list_user_reservations(
    db: AsyncSession,
    current_user: User,
    params: ReservationListParams,
) -> PaginatedReservationResponse:
    reservations, total = await reservation_repository.get_list_by_user(
        db,
        current_user.id,
        offset=params.offset,
        limit=params.limit,
        status=params.status,
    )
    return PaginatedReservationResponse(
        items=[ReservationResponse.model_validate(r) for r in reservations],
        total=total,
        offset=params.offset,
        limit=params.limit,
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
