"""Repozytorium wewnętrznych notatek o kliencie — czysty SQL (asyncpg)."""

import uuid

from app.db.session import Db
from app.models.customer_note import CustomerNote
from app.repositories import _relations


async def _attach_author(db: Db, notes: list[CustomerNote]) -> None:
    if not notes:
        return
    users = await _relations.load_users_for(db, [n.author_id for n in notes])
    for note in notes:
        note.author = users.get(note.author_id)


async def list_for_customer(db: Db, customer_id: uuid.UUID) -> list[CustomerNote]:
    rows = await db.fetch(
        "SELECT * FROM customer_notes WHERE customer_id = $1 ORDER BY created_at DESC",
        customer_id,
    )
    notes = [CustomerNote.from_row(r) for r in rows]
    await _attach_author(db, notes)
    return notes


async def get_by_id(db: Db, note_id: uuid.UUID) -> CustomerNote | None:
    row = await db.fetchrow("SELECT * FROM customer_notes WHERE id = $1", note_id)
    if row is None:
        return None
    note = CustomerNote.from_row(row)
    await _attach_author(db, [note])
    return note


async def create(db: Db, note: CustomerNote) -> CustomerNote:
    row = await db.fetchrow(
        "INSERT INTO customer_notes (id, customer_id, author_id, body) "
        "VALUES ($1, $2, $3, $4) RETURNING *",
        note.id,
        note.customer_id,
        note.author_id,
        note.body,
    )
    assert row is not None
    created = CustomerNote.from_row(row)
    await _attach_author(db, [created])
    return created


async def update(db: Db, note: CustomerNote) -> CustomerNote:
    row = await db.fetchrow(
        "UPDATE customer_notes SET body = $2, updated_at = now() WHERE id = $1 RETURNING *",
        note.id,
        note.body,
    )
    assert row is not None
    updated = CustomerNote.from_row(row)
    await _attach_author(db, [updated])
    return updated


async def delete(db: Db, note: CustomerNote) -> None:
    await db.execute("DELETE FROM customer_notes WHERE id = $1", note.id)
