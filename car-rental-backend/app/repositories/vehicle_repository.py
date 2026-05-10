"""Repozytorium pojazdów — zapytania o katalog, dostępność, panel admina.

Wspiera filtrowanie po kategorii/silniku/cenie, sprawdzanie kolizji
rezerwacji w zadanym przedziale dat oraz operacje CRUD wykorzystywane
przez serwis pojazdów.
"""

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, or_ as sa_or, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from app.core.utils import date_to_utc_datetime
from app.models.category import Category, CategoryName
from app.models.rental import Reservation, ReservationStatus
from app.models.vehicle import EngineType, Vehicle, VehicleStatus
from app.models.vehicle_image import VehicleImage

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
    status_in: list[VehicleStatus] | None = None,
    search: str | None = None,
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
    if status_in is not None:
        # Used by the public catalog to hide statuses that aren't customer-facing
        # (MAINTENANCE / OUT_OF_SERVICE) without baking that policy into the model.
        stmt = stmt.where(Vehicle.status.in_(status_in))
    if search:
        # Free-text search across the operator-relevant identifiers
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            sa_or(
                Vehicle.brand.ilike(like),
                Vehicle.model.ilike(like),
                Vehicle.license_plate.ilike(like),
                Vehicle.vin.ilike(like),
            )
        )
    return stmt


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
    status_in: list[VehicleStatus] | None = None,
    available_from: date | None = None,
    available_to: date | None = None,
    search: str | None = None,
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
        status_in=status_in,
        search=search,
    )

    if available_from is not None and available_to is not None:
        conflicting = (
            select(Reservation.vehicle_id)
            .where(
                Reservation.status.in_(BLOCKING_STATUSES),
                Reservation.start_date < _date_to_datetime_end(available_to),
                Reservation.end_date > date_to_utc_datetime(available_from),
            )
            .scalar_subquery()
        )
        base = base.where(Vehicle.id.not_in(conflicting))

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, Vehicle.created_at)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()

    stmt = (
        base.options(
            contains_eager(Vehicle.category),
            selectinload(Vehicle.images),
        )
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    vehicles = list(result.scalars().unique())

    return vehicles, total


async def get_by_id(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
    stmt = (
        select(Vehicle)
        .options(joinedload(Vehicle.category), selectinload(Vehicle.images))
        .where(Vehicle.id == vehicle_id, Vehicle.is_active.is_(True))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id_for_update(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
    """Fetch vehicle and lock its row for the duration of the transaction.

    Use this instead of get_by_id when you need to serialize concurrent writes
    (e.g. availability check + reservation insert).
    """
    await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id).with_for_update())
    return await get_by_id(db, vehicle_id)


async def count_conflicting_reservations(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> int:
    # Klasyczny wzorzec na nakładające się przedziały:
    # rezerwacje kolidują gdy A.start < B.end AND A.end > B.start
    stmt = select(func.count()).where(
        Reservation.vehicle_id == vehicle_id,
        Reservation.status.in_(BLOCKING_STATUSES),
        Reservation.start_date < _date_to_datetime_end(end_date),
        Reservation.end_date > date_to_utc_datetime(start_date),
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def has_blocking_reservations(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> bool:
    """Return True if vehicle has any pending/confirmed/active reservation."""
    stmt = (
        select(Reservation.id)
        .where(
            Reservation.vehicle_id == vehicle_id,
            Reservation.status.in_(BLOCKING_STATUSES),
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def create(db: AsyncSession, vehicle: Vehicle) -> Vehicle:
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def update(db: AsyncSession, vehicle: Vehicle) -> Vehicle:
    await db.flush()
    await db.refresh(vehicle)
    return vehicle


async def soft_delete(db: AsyncSession, vehicle: Vehicle) -> Vehicle:
    vehicle.is_active = False
    await db.flush()
    return vehicle


async def bulk_update_status(
    db: AsyncSession,
    ids: list[uuid.UUID],
    status: VehicleStatus,
) -> tuple[int, list[uuid.UUID]]:
    """Update status for many vehicles in one statement.

    Returns ``(updated_count, missing_ids)`` — missing covers ids that don't
    exist or were soft-deleted, so the caller can surface them as a 207-style
    partial-success payload.
    """
    if not ids:
        return 0, []

    existing_stmt = select(Vehicle.id).where(
        Vehicle.id.in_(ids), Vehicle.is_active.is_(True)
    )
    existing = {row for row in (await db.execute(existing_stmt)).scalars()}
    missing = [vid for vid in ids if vid not in existing]

    if not existing:
        return 0, missing

    await db.execute(
        sa_update(Vehicle)
        .where(Vehicle.id.in_(existing), Vehicle.is_active.is_(True))
        .values(status=status)
    )
    await db.flush()
    return len(existing), missing


async def _lock_vehicle_row(db: AsyncSession, vehicle_id: uuid.UUID) -> None:
    """Take a FOR UPDATE lock on the parent vehicle row.

    Used by image mutation paths so the "exactly one primary image per vehicle"
    invariant is serialized against concurrent writers. The lock is released
    automatically when the surrounding transaction commits or rolls back.
    """
    await db.execute(select(Vehicle.id).where(Vehicle.id == vehicle_id).with_for_update())


async def add_image(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    url: str,
    is_primary: bool,
) -> VehicleImage:
    await _lock_vehicle_row(db, vehicle_id)
    # Append to the end — position computed inside the same transaction so a
    # racing parallel upload would just produce equal positions, not gaps.
    next_position_stmt = select(func.coalesce(func.max(VehicleImage.position) + 1, 0)).where(
        VehicleImage.vehicle_id == vehicle_id
    )
    next_position = (await db.execute(next_position_stmt)).scalar_one()

    if is_primary:
        # Demote whatever was primary before — partial unique index would 23505
        await db.execute(
            sa_update(VehicleImage)
            .where(VehicleImage.vehicle_id == vehicle_id, VehicleImage.is_primary.is_(True))
            .values(is_primary=False)
        )

    image = VehicleImage(
        vehicle_id=vehicle_id,
        url=url,
        position=next_position,
        is_primary=is_primary,
    )
    db.add(image)
    await db.flush()
    await db.refresh(image)
    return image


async def get_image(db: AsyncSession, image_id: uuid.UUID) -> VehicleImage | None:
    return await db.get(VehicleImage, image_id)


async def delete_image(db: AsyncSession, image: VehicleImage) -> None:
    was_primary = image.is_primary
    vehicle_id = image.vehicle_id
    await _lock_vehicle_row(db, vehicle_id)
    await db.delete(image)
    await db.flush()

    # If the deleted one was primary, promote the lowest-position remaining
    # image so the vehicle still has a primary image to render.
    if was_primary:
        next_primary_stmt = (
            select(VehicleImage)
            .where(VehicleImage.vehicle_id == vehicle_id)
            .order_by(VehicleImage.position)
            .limit(1)
        )
        next_primary = (await db.execute(next_primary_stmt)).scalar_one_or_none()
        if next_primary is not None:
            next_primary.is_primary = True
            await db.flush()


async def set_primary_image(db: AsyncSession, image: VehicleImage) -> None:
    if image.is_primary:
        return
    await _lock_vehicle_row(db, image.vehicle_id)
    await db.execute(
        sa_update(VehicleImage)
        .where(VehicleImage.vehicle_id == image.vehicle_id, VehicleImage.is_primary.is_(True))
        .values(is_primary=False)
    )
    image.is_primary = True
    await db.flush()


async def reorder_images(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    ordered_ids: list[uuid.UUID],
) -> list[VehicleImage]:
    """Apply a new ``position`` to each image in the order given.

    Ids not belonging to the vehicle are silently skipped (caller validates).
    """
    stmt = select(VehicleImage).where(VehicleImage.vehicle_id == vehicle_id)
    images = {img.id: img for img in (await db.execute(stmt)).scalars()}
    for index, img_id in enumerate(ordered_ids):
        if img_id in images:
            images[img_id].position = index
    await db.flush()
    return sorted(images.values(), key=lambda i: i.position)


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
