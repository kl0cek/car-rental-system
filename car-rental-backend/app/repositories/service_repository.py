"""Repozytorium zleceń serwisowych i historii serwisu.

Zawiera wyłącznie operacje CRUD — logika biznesowa (np. zmiana statusu
po zakończeniu pracy, walidacja kolejności statusów) trafia do
warstwy serwisowej, gdy będzie tworzona.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.service_history import ServiceHistory
from app.models.service_order import ServiceOrder


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


async def list_orders_for_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[ServiceOrder]:
    stmt = (
        select(ServiceOrder)
        .where(ServiceOrder.vehicle_id == vehicle_id)
        .order_by(ServiceOrder.scheduled_date.desc())
    )
    return list((await db.execute(stmt)).scalars())


async def update_order(db: AsyncSession, order: ServiceOrder) -> ServiceOrder:
    await db.flush()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order: ServiceOrder) -> None:
    await db.delete(order)
    await db.flush()


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
