"""Repozytorium rezerwacji — zapytania o `reservations` z eager-load pojazdu.

Obsługuje listing rezerwacji per użytkownik, paginację oraz wyszukiwanie
po statusach (np. aktywne / nadchodzące).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.rental import Reservation, ReservationStatus
from app.models.vehicle import Vehicle

SORTABLE_COLUMNS = {
    "created_at": Reservation.created_at,
    "start_date": Reservation.start_date,
    "end_date": Reservation.end_date,
    "total_price": Reservation.total_price,
}


async def get_by_id(db: AsyncSession, reservation_id: uuid.UUID) -> Reservation | None:
    stmt = (
        select(Reservation)
        .options(
            joinedload(Reservation.vehicle).selectinload(Vehicle.images),
            joinedload(Reservation.user),
        )
        .where(Reservation.id == reservation_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id_for_update(db: AsyncSession, reservation_id: uuid.UUID) -> Reservation | None:
    """Zablokuj wiersz rezerwacji, a następnie zwróć ją z eager-loadem pojazdu/użytkownika.

    Blokada i eager-load są celowo rozdzielone na dwa zapytania: połączenie
    `FOR UPDATE` z `joinedload` (czyli LEFT OUTER JOIN) jest odrzucane przez
    PostgreSQL — "FOR UPDATE cannot be applied to the nullable side of an outer join".
    Najpierw więc blokujemy sam wiersz `reservations` (bez joinów), potem dociągamy
    relacje przez `get_by_id`. Ten sam wzorzec stosuje `vehicle_repository`.
    """
    await db.execute(select(Reservation).where(Reservation.id == reservation_id).with_for_update())
    return await get_by_id(db, reservation_id)


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
        .options(joinedload(Reservation.vehicle).selectinload(Vehicle.images))
        .where(Reservation.user_id == user_id)
    )
    if status is not None:
        count_stmt = count_stmt.where(Reservation.status == status)
        data_stmt = data_stmt.where(Reservation.status == status)

    total = (await db.execute(count_stmt)).scalar_one()

    data_stmt = data_stmt.order_by(Reservation.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(data_stmt)
    return list(result.scalars().unique()), total


async def get_admin_list(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    status: ReservationStatus | None = None,
    user_id: uuid.UUID | None = None,
    vehicle_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Reservation], int]:
    base = select(Reservation)
    if status is not None:
        base = base.where(Reservation.status == status)
    if user_id is not None:
        base = base.where(Reservation.user_id == user_id)
    if vehicle_id is not None:
        base = base.where(Reservation.vehicle_id == vehicle_id)
    # Overlap semantics: include reservations whose interval intersects [date_from, date_to].
    if date_from is not None:
        base = base.where(Reservation.end_date >= date_from)
    if date_to is not None:
        base = base.where(Reservation.start_date <= date_to)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, Reservation.created_at)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    stmt = (
        base.options(
            joinedload(Reservation.user),
            joinedload(Reservation.vehicle).selectinload(Vehicle.images),
        )
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
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
    # Re-fetch with vehicle.images eager-loaded so callers building response DTOs
    # don't trigger an implicit lazy load (which fails under async sessions).
    stmt = (
        select(Reservation)
        .options(joinedload(Reservation.vehicle).selectinload(Vehicle.images))
        .where(Reservation.id == reservation.id)
    )
    return (await db.execute(stmt)).scalar_one()


async def update_status(
    db: AsyncSession,
    reservation: Reservation,
    new_status: ReservationStatus,
) -> Reservation:
    reservation.status = new_status
    await db.flush()
    return reservation
