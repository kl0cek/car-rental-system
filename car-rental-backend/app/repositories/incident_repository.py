"""Repozytorium incydentów odnotowanych przez pracownika dla klienta (SQL)."""

import uuid

from app.db.session import Db
from app.models.incident import Incident
from app.repositories import _relations


async def _attach_reporter(db: Db, incidents: list[Incident]) -> None:
    if not incidents:
        return
    users = await _relations.load_users_for(db, [i.reported_by_id for i in incidents])
    for incident in incidents:
        incident.reported_by = users.get(incident.reported_by_id)


async def list_for_customer(db: Db, customer_id: uuid.UUID) -> list[Incident]:
    rows = await db.fetch(
        "SELECT * FROM incidents WHERE customer_id = $1 ORDER BY created_at DESC", customer_id
    )
    incidents = [Incident.from_row(r) for r in rows]
    await _attach_reporter(db, incidents)
    return incidents


async def get_by_id(db: Db, incident_id: uuid.UUID) -> Incident | None:
    row = await db.fetchrow("SELECT * FROM incidents WHERE id = $1", incident_id)
    if row is None:
        return None
    incident = Incident.from_row(row)
    await _attach_reporter(db, [incident])
    return incident


async def count_for_customer(db: Db, customer_id: uuid.UUID) -> int:
    total = await db.fetchval("SELECT count(*) FROM incidents WHERE customer_id = $1", customer_id)
    return int(total or 0)


async def create(db: Db, incident: Incident) -> Incident:
    row = await db.fetchrow(
        "INSERT INTO incidents (id, customer_id, rental_id, reported_by_id, type, severity, "
        "title, description, cost) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *",
        incident.id,
        incident.customer_id,
        incident.rental_id,
        incident.reported_by_id,
        incident.type.value,
        incident.severity.value,
        incident.title,
        incident.description,
        incident.cost,
    )
    assert row is not None
    created = Incident.from_row(row)
    await _attach_reporter(db, [created])
    return created


async def delete(db: Db, incident: Incident) -> None:
    await db.execute("DELETE FROM incidents WHERE id = $1", incident.id)
