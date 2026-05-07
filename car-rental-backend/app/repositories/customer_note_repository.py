"""Repozytorium wewnętrznych notatek o kliencie."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.customer_note import CustomerNote


async def list_for_customer(
    db: AsyncSession,
    customer_id: uuid.UUID,
) -> list[CustomerNote]:
    stmt = (
        select(CustomerNote)
        .options(joinedload(CustomerNote.author))
        .where(CustomerNote.customer_id == customer_id)
        .order_by(CustomerNote.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars())


async def get_by_id(
    db: AsyncSession,
    note_id: uuid.UUID,
) -> CustomerNote | None:
    stmt = (
        select(CustomerNote)
        .options(joinedload(CustomerNote.author))
        .where(CustomerNote.id == note_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create(db: AsyncSession, note: CustomerNote) -> CustomerNote:
    db.add(note)
    await db.flush()
    return await get_by_id(db, note.id)  # type: ignore[return-value]


async def update(db: AsyncSession, note: CustomerNote) -> CustomerNote:
    await db.flush()
    return await get_by_id(db, note.id)  # type: ignore[return-value]


async def delete(db: AsyncSession, note: CustomerNote) -> None:
    await db.delete(note)
    await db.flush()
