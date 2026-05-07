"""Repozytorium incydentów odnotowanych przez pracownika dla klienta."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.incident import Incident


async def list_for_customer(
    db: AsyncSession,
    customer_id: uuid.UUID,
) -> list[Incident]:
    stmt = (
        select(Incident)
        .options(joinedload(Incident.reported_by))
        .where(Incident.customer_id == customer_id)
        .order_by(Incident.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars())


async def get_by_id(
    db: AsyncSession,
    incident_id: uuid.UUID,
) -> Incident | None:
    stmt = (
        select(Incident)
        .options(joinedload(Incident.reported_by))
        .where(Incident.id == incident_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def count_for_customer(
    db: AsyncSession,
    customer_id: uuid.UUID,
) -> int:
    stmt = select(func.count(Incident.id)).where(Incident.customer_id == customer_id)
    return (await db.execute(stmt)).scalar_one()


async def create(db: AsyncSession, incident: Incident) -> Incident:
    db.add(incident)
    await db.flush()
    # Re-fetch with reported_by eager-loaded for the response DTO
    return await get_by_id(db, incident.id)  # type: ignore[return-value]


async def delete(db: AsyncSession, incident: Incident) -> None:
    await db.delete(incident)
    await db.flush()
