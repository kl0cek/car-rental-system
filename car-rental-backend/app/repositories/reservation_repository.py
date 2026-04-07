import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.rental import Reservation, ReservationStatus


async def get_by_id(db: AsyncSession, reservation_id: uuid.UUID) -> Reservation | None:
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.vehicle), joinedload(Reservation.user))
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_list_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
    status: ReservationStatus | None = None,
) -> tuple[list[Reservation], int]:
    count_stmt = select(func.count(Reservation.id)).where(Reservation.user_id == user_id)
    data_stmt = (
        select(Reservation)
        .options(joinedload(Reservation.vehicle))
        .where(Reservation.user_id == user_id)
    )
    if status is not None:
        count_stmt = count_stmt.where(Reservation.status == status)
        data_stmt = data_stmt.where(Reservation.status == status)

    total = (await db.execute(count_stmt)).scalar_one()

    data_stmt = data_stmt.order_by(Reservation.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(data_stmt)
    return list(result.scalars().unique()), total


async def create(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
    total_price: Decimal,
) -> Reservation:
    reservation = Reservation(
        user_id=user_id,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status=ReservationStatus.PENDING,
    )
    db.add(reservation)
    await db.flush()
    await db.refresh(reservation, ["vehicle"])
    return reservation


async def update_status(
    db: AsyncSession,
    reservation: Reservation,
    new_status: ReservationStatus,
) -> Reservation:
    reservation.status = new_status
    await db.flush()
    return reservation
