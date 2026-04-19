import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from app.models.rental import Rental, RentalPriceBreakdown, Reservation, ReservationStatus

SORTABLE_COLUMNS = {
    "pickup_date": Rental.pickup_date,
    "return_date": Rental.return_date,
    "created_at": Rental.created_at,
}


async def get_by_id(db: AsyncSession, rental_id: uuid.UUID) -> Rental | None:
    stmt = (
        select(Rental)
        .options(
            joinedload(Rental.price_breakdown),
            joinedload(Rental.reservation),
        )
        .where(Rental.id == rental_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_reservation_id(db: AsyncSession, reservation_id: uuid.UUID) -> Rental | None:
    stmt = select(Rental).where(Rental.reservation_id == reservation_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_pickup(
    db: AsyncSession,
    *,
    reservation_id: uuid.UUID,
    employee_id: uuid.UUID,
    mileage_start: int,
    fuel_level_start: Decimal,
    pickup_date: datetime,
) -> Rental:
    rental = Rental(
        reservation_id=reservation_id,
        employee_id=employee_id,
        mileage_start=mileage_start,
        fuel_level_start=fuel_level_start,
        pickup_date=pickup_date,
    )
    db.add(rental)
    await db.flush()
    await db.refresh(rental, ["price_breakdown"])
    return rental


async def update_return(
    db: AsyncSession,
    rental: Rental,
    *,
    mileage_end: int,
    fuel_level_end: Decimal,
    damage_notes: str | None,
    return_date: datetime,
) -> Rental:
    rental.mileage_end = mileage_end
    rental.fuel_level_end = fuel_level_end
    rental.damage_notes = damage_notes
    rental.return_date = return_date
    await db.flush()
    return rental


async def get_list_by_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "pickup_date",
    sort_order: str = "desc",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: ReservationStatus | None = None,
) -> tuple[list[Rental], int]:
    base = (
        select(Rental)
        .join(Rental.reservation)
        .where(Reservation.user_id == user_id)
    )
    if status is not None:
        base = base.where(Reservation.status == status)
    if date_from is not None:
        base = base.where(Rental.pickup_date >= date_from)
    if date_to is not None:
        base = base.where(Rental.pickup_date <= date_to)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, Rental.pickup_date)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()
    if sort_by == "return_date":
        order = order.nulls_last() if sort_order == "desc" else order.nulls_first()

    stmt = (
        base.options(
            contains_eager(Rental.reservation).joinedload(Reservation.vehicle),
            joinedload(Rental.price_breakdown),
        )
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique()), total


async def create_price_breakdown(
    db: AsyncSession,
    *,
    rental_id: uuid.UUID,
    base_price: Decimal,
    fuel_surcharge: Decimal,
    risk_multiplier: Decimal,
    final_price: Decimal,
) -> RentalPriceBreakdown:
    breakdown = RentalPriceBreakdown(
        rental_id=rental_id,
        base_price=base_price,
        fuel_surcharge=fuel_surcharge,
        risk_multiplier=risk_multiplier,
        final_price=final_price,
    )
    db.add(breakdown)
    await db.flush()
    await db.refresh(breakdown)
    return breakdown
