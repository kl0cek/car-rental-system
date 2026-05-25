"""Repozytorium zleceń serwisowych i historii serwisu.

Zawiera wyłącznie operacje CRUD i odczytowe — logika biznesowa
(automatyczna zmiana statusu pojazdu, blokada rezerwacji, walidacja
kolejności statusów) trafia do warstwy serwisowej.
"""

import uuid
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.service_history import ServiceHistory
from app.models.service_order import ServiceOrder, ServiceOrderStatus, ServiceType

SORTABLE_COLUMNS = {
    "scheduled_date": ServiceOrder.scheduled_date,
    "completed_date": ServiceOrder.completed_date,
    "created_at": ServiceOrder.created_at,
    "cost": ServiceOrder.cost,
}


def _apply_filters(
    stmt: Select[tuple[ServiceOrder]],
    *,
    status: ServiceOrderStatus | None,
    status_in: list[ServiceOrderStatus] | None,
    vehicle_id: uuid.UUID | None,
    technician_id: uuid.UUID | None,
    type_: ServiceType | None,
    scheduled_from: datetime | None,
    scheduled_to: datetime | None,
) -> Select[tuple[ServiceOrder]]:
    if status is not None:
        stmt = stmt.where(ServiceOrder.status == status)
    if status_in:
        stmt = stmt.where(ServiceOrder.status.in_(status_in))
    if vehicle_id is not None:
        stmt = stmt.where(ServiceOrder.vehicle_id == vehicle_id)
    if technician_id is not None:
        stmt = stmt.where(ServiceOrder.technician_id == technician_id)
    if type_ is not None:
        stmt = stmt.where(ServiceOrder.type == type_)
    if scheduled_from is not None:
        stmt = stmt.where(ServiceOrder.scheduled_date >= scheduled_from)
    if scheduled_to is not None:
        stmt = stmt.where(ServiceOrder.scheduled_date <= scheduled_to)
    return stmt


async def create_order(db: AsyncSession, order: ServiceOrder) -> ServiceOrder:
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def get_order_by_id(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> ServiceOrder | None:
    stmt = (
        select(ServiceOrder)
        .options(
            joinedload(ServiceOrder.vehicle),
            joinedload(ServiceOrder.technician),
            selectinload(ServiceOrder.history_entries),
        )
        .where(ServiceOrder.id == order_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_order_by_id_for_update(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> ServiceOrder | None:
    """Lock the row so concurrent status transitions cannot interleave."""
    await db.execute(select(ServiceOrder.id).where(ServiceOrder.id == order_id).with_for_update())
    return await get_order_by_id(db, order_id)


async def list_orders(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "scheduled_date",
    sort_order: str = "desc",
    status: ServiceOrderStatus | None = None,
    status_in: list[ServiceOrderStatus] | None = None,
    vehicle_id: uuid.UUID | None = None,
    technician_id: uuid.UUID | None = None,
    type_: ServiceType | None = None,
    scheduled_from: datetime | None = None,
    scheduled_to: datetime | None = None,
) -> tuple[list[ServiceOrder], int]:
    base = select(ServiceOrder)
    base = _apply_filters(
        base,
        status=status,
        status_in=status_in,
        vehicle_id=vehicle_id,
        technician_id=technician_id,
        type_=type_,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_col = SORTABLE_COLUMNS.get(sort_by, ServiceOrder.scheduled_date)
    order = sort_col.asc() if sort_order == "asc" else sort_col.desc()
    # ``completed_date`` and ``cost`` are nullable — keep NULLs at the tail when
    # sorting descending so the user-visible "no value yet" rows don't dominate.
    if sort_by in ("completed_date", "cost"):
        order = order.nulls_last() if sort_order == "desc" else order.nulls_first()

    stmt = (
        base.options(
            joinedload(ServiceOrder.vehicle),
            joinedload(ServiceOrder.technician),
        )
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique()), total


async def list_orders_for_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[ServiceOrder]:
    stmt = (
        select(ServiceOrder)
        .options(
            joinedload(ServiceOrder.technician),
            selectinload(ServiceOrder.history_entries),
        )
        .where(ServiceOrder.vehicle_id == vehicle_id)
        .order_by(ServiceOrder.scheduled_date.desc())
    )
    return list((await db.execute(stmt)).scalars().unique())


async def update_order(db: AsyncSession, order: ServiceOrder) -> ServiceOrder:
    await db.flush()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order: ServiceOrder) -> None:
    await db.delete(order)
    await db.flush()


async def count_by_status(db: AsyncSession) -> dict[ServiceOrderStatus, int]:
    """Return total order count grouped by status — feeds the panel statistics."""
    stmt = select(ServiceOrder.status, func.count(ServiceOrder.id)).group_by(ServiceOrder.status)
    rows = (await db.execute(stmt)).all()
    counts: dict[ServiceOrderStatus, int] = {s: 0 for s in ServiceOrderStatus}
    for status_value, count in rows:
        counts[status_value] = count
    return counts


async def has_active_service_for_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> bool:
    """True if vehicle has any SCHEDULED/IN_PROGRESS service order.

    Used by the reservation flow so we don't accept bookings on a car the
    technician panel has already pulled off the road.
    """
    stmt = (
        select(ServiceOrder.id)
        .where(
            ServiceOrder.vehicle_id == vehicle_id,
            ServiceOrder.status.in_(
                (ServiceOrderStatus.SCHEDULED, ServiceOrderStatus.IN_PROGRESS),
            ),
        )
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none() is not None


async def create_history(db: AsyncSession, entry: ServiceHistory) -> ServiceHistory:
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_history_for_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[ServiceHistory]:
    stmt = (
        select(ServiceHistory)
        .where(ServiceHistory.vehicle_id == vehicle_id)
        .order_by(ServiceHistory.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars())


async def list_history_for_order(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> list[ServiceHistory]:
    stmt = (
        select(ServiceHistory)
        .where(ServiceHistory.service_order_id == order_id)
        .order_by(ServiceHistory.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars())
