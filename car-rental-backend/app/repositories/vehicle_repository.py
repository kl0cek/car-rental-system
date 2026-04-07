import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from app.models.category import Category, CategoryName
from app.models.rental import Reservation, ReservationStatus
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

SORTABLE_COLUMNS = {
    "brand": Vehicle.brand,
    "model": Vehicle.model,
    "year": Vehicle.year,
    "daily_base_price": Vehicle.daily_base_price,
    "created_at": Vehicle.created_at,
    "mileage": Vehicle.mileage,
    "horsepower": Vehicle.horsepower,
}

BLOCKING_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.ACTIVE,
)


def _apply_filters(
    stmt: Select[Any],
    *,
    category: CategoryName | None = None,
    engine_type: EngineType | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    min_year: int | None = None,
    max_year: int | None = None,
    min_seats: int | None = None,
    status: VehicleStatus | None = None,
) -> Select[Any]:
    if category is not None:
        stmt = stmt.where(Category.name == category)
    if engine_type is not None:
        stmt = stmt.where(Vehicle.engine_type == engine_type)
    if min_price is not None:
        stmt = stmt.where(Vehicle.daily_base_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Vehicle.daily_base_price <= max_price)
    if min_year is not None:
        stmt = stmt.where(Vehicle.year >= min_year)
    if max_year is not None:
        stmt = stmt.where(Vehicle.year <= max_year)
    if min_seats is not None:
        stmt = stmt.where(Vehicle.seats >= min_seats)
    if status is not None:
        stmt = stmt.where(Vehicle.status == status)
    return stmt


def _date_to_datetime(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=UTC)


def _date_to_datetime_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=UTC)


async def get_list(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    category: CategoryName | None = None,
    engine_type: EngineType | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    min_year: int | None = None,
    max_year: int | None = None,
    min_seats: int | None = None,
    status: VehicleStatus | None = None,
    available_from: date | None = None,
    available_to: date | None = None,
) -> tuple[list[Vehicle], int]:
    base = select(Vehicle).join(Vehicle.category).where(Vehicle.is_active.is_(True))
    base = _apply_filters(
        base,
        category=category,
        engine_type=engine_type,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        min_seats=min_seats,
        status=status,
    )

    if available_from is not None and available_to is not None:
        conflicting = (
            select(Reservation.vehicle_id)
            .where(
                Reservation.status.in_(BLOCKING_STATUSES),
                Reservation.start_date < _date_to_datetime_end(available_to),
                Reservation.end_date > _date_to_datetime(available_from),
            )
            .scalar_subquery()
        )
        base = base.where(Vehicle.id.not_in(conflicting))

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, Vehicle.created_at)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    stmt = (
        base.options(contains_eager(Vehicle.category)).order_by(order).offset(offset).limit(limit)
    )
    result = await db.execute(stmt)
    vehicles = list(result.scalars().unique())

    return vehicles, total


async def get_by_id(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
    stmt = (
        select(Vehicle)
        .options(joinedload(Vehicle.category))
        .where(Vehicle.id == vehicle_id, Vehicle.is_active.is_(True))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def count_conflicting_reservations(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> int:
    locked_subq = (
        select(Reservation.id)
        .where(
            Reservation.vehicle_id == vehicle_id,
            Reservation.status.in_(BLOCKING_STATUSES),
            Reservation.start_date < _date_to_datetime_end(end_date),
            Reservation.end_date > _date_to_datetime(start_date),
        )
        .with_for_update()
        .subquery()
    )
    stmt = select(func.count()).select_from(locked_subq)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_booked_dates(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[dict[str, Any]]:
    stmt = (
        select(Reservation.start_date, Reservation.end_date)
        .where(
            Reservation.vehicle_id == vehicle_id,
            Reservation.status.in_(BLOCKING_STATUSES),
            Reservation.end_date > func.now(),
        )
        .order_by(Reservation.start_date)
    )
    result = await db.execute(stmt)
    return [{"start_date": row.start_date, "end_date": row.end_date} for row in result.all()]
