"""Repozytorium zleceń serwisowych i historii serwisu — czysty SQL (asyncpg).

Wyłącznie operacje CRUD i odczytowe — logika biznesowa (zmiana statusu
pojazdu, walidacja kolejności statusów) jest w warstwie serwisowej.
Pojazd, technik i historia dociągane są osobnymi zapytaniami.
"""

import uuid
from datetime import datetime
from typing import Any

from app.db.session import Db
from app.models.service_history import ServiceHistory
from app.models.service_order import ServiceOrder, ServiceOrderStatus, ServiceType
from app.repositories import _relations

SORTABLE_COLUMNS = {
    "scheduled_date": "scheduled_date",
    "completed_date": "completed_date",
    "created_at": "created_at",
    "cost": "cost",
}

_ACTIVE_STATUSES = [ServiceOrderStatus.SCHEDULED.value, ServiceOrderStatus.IN_PROGRESS.value]


async def _load_history_map(
    db: Db, order_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[ServiceHistory]]:
    if not order_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM service_history WHERE service_order_id = ANY($1::uuid[]) "
        "ORDER BY created_at DESC",
        list(set(order_ids)),
    )
    result: dict[uuid.UUID, list[ServiceHistory]] = {}
    for row in rows:
        result.setdefault(row["service_order_id"], []).append(ServiceHistory.from_row(row))
    return result


async def _attach_orders(db: Db, orders: list[ServiceOrder], *, with_history: bool) -> None:
    if not orders:
        return
    vehicles = await _relations.load_vehicles_for(db, [o.vehicle_id for o in orders])
    technicians = await _relations.load_users_for(db, [o.technician_id for o in orders])
    for order in orders:
        order.vehicle = vehicles.get(order.vehicle_id)
        order.technician = technicians.get(order.technician_id)
    if with_history:
        history = await _load_history_map(db, [o.id for o in orders])
        for order in orders:
            order.history_entries = history.get(order.id, [])


async def create_order(db: Db, order: ServiceOrder) -> ServiceOrder:
    row = await db.fetchrow(
        "INSERT INTO service_orders (id, vehicle_id, type, status, description, cost, "
        "scheduled_date, completed_date, technician_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *",
        order.id,
        order.vehicle_id,
        order.type.value,
        order.status.value,
        order.description,
        order.cost,
        order.scheduled_date,
        order.completed_date,
        order.technician_id,
    )
    assert row is not None
    created = ServiceOrder.from_row(row)
    await _attach_orders(db, [created], with_history=True)
    return created


async def get_order_by_id(db: Db, order_id: uuid.UUID) -> ServiceOrder | None:
    row = await db.fetchrow("SELECT * FROM service_orders WHERE id = $1", order_id)
    if row is None:
        return None
    order = ServiceOrder.from_row(row)
    await _attach_orders(db, [order], with_history=True)
    return order


async def get_order_by_id_for_update(db: Db, order_id: uuid.UUID) -> ServiceOrder | None:
    """Zablokuj wiersz, by równoległe zmiany statusu się nie przeplotły."""
    await db.execute("SELECT id FROM service_orders WHERE id = $1 FOR UPDATE", order_id)
    return await get_order_by_id(db, order_id)


async def list_orders(
    db: Db,
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
    conditions: list[str] = []
    args: list[Any] = []

    def add(template: str, value: Any) -> None:
        args.append(value)
        conditions.append(template.format(n=len(args)))

    if status is not None:
        add("status = ${n}", status.value)
    if status_in:
        add("status = ANY(${n}::text[])", [s.value for s in status_in])
    if vehicle_id is not None:
        add("vehicle_id = ${n}", vehicle_id)
    if technician_id is not None:
        add("technician_id = ${n}", technician_id)
    if type_ is not None:
        add("type = ${n}", type_.value)
    if scheduled_from is not None:
        add("scheduled_date >= ${n}", scheduled_from)
    if scheduled_to is not None:
        add("scheduled_date <= ${n}", scheduled_to)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = await db.fetchval(f"SELECT count(*) FROM service_orders{where}", *args)

    sort_col = SORTABLE_COLUMNS.get(sort_by, "scheduled_date")
    direction = "ASC" if sort_order == "asc" else "DESC"
    nulls = ""
    if sort_by in ("completed_date", "cost"):
        nulls = " NULLS LAST" if sort_order == "desc" else " NULLS FIRST"

    rows = await db.fetch(
        f"SELECT * FROM service_orders{where} ORDER BY {sort_col} {direction}{nulls} "
        f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    orders = [ServiceOrder.from_row(r) for r in rows]
    await _attach_orders(db, orders, with_history=False)
    return orders, int(total or 0)


async def list_orders_for_vehicle(db: Db, vehicle_id: uuid.UUID) -> list[ServiceOrder]:
    rows = await db.fetch(
        "SELECT * FROM service_orders WHERE vehicle_id = $1 ORDER BY scheduled_date DESC",
        vehicle_id,
    )
    orders = [ServiceOrder.from_row(r) for r in rows]
    await _attach_orders(db, orders, with_history=True)
    return orders


async def update_order(db: Db, order: ServiceOrder) -> ServiceOrder:
    row = await db.fetchrow(
        "UPDATE service_orders SET type = $2, status = $3, description = $4, cost = $5, "
        "scheduled_date = $6, completed_date = $7, technician_id = $8, updated_at = now() "
        "WHERE id = $1 RETURNING *",
        order.id,
        order.type.value,
        order.status.value,
        order.description,
        order.cost,
        order.scheduled_date,
        order.completed_date,
        order.technician_id,
    )
    assert row is not None
    updated = ServiceOrder.from_row(row)
    await _attach_orders(db, [updated], with_history=True)
    return updated


async def delete_order(db: Db, order: ServiceOrder) -> None:
    await db.execute("DELETE FROM service_orders WHERE id = $1", order.id)


async def count_by_status(db: Db) -> dict[ServiceOrderStatus, int]:
    """Liczba zleceń pogrupowana po statusie — zasila karty statystyk panelu."""
    rows = await db.fetch("SELECT status, count(*) AS n FROM service_orders GROUP BY status")
    counts: dict[ServiceOrderStatus, int] = {s: 0 for s in ServiceOrderStatus}
    for row in rows:
        counts[ServiceOrderStatus(row["status"])] = int(row["n"])
    return counts


async def has_active_service_for_vehicle(db: Db, vehicle_id: uuid.UUID) -> bool:
    """True, jeśli pojazd ma jakiekolwiek zlecenie SCHEDULED/IN_PROGRESS."""
    row = await db.fetchrow(
        "SELECT 1 FROM service_orders WHERE vehicle_id = $1 AND status = ANY($2::text[]) LIMIT 1",
        vehicle_id,
        _ACTIVE_STATUSES,
    )
    return row is not None


async def create_history(db: Db, entry: ServiceHistory) -> ServiceHistory:
    row = await db.fetchrow(
        "INSERT INTO service_history (id, vehicle_id, service_order_id, notes, parts_replaced, "
        "mileage_at_service) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
        entry.id,
        entry.vehicle_id,
        entry.service_order_id,
        entry.notes,
        entry.parts_replaced,
        entry.mileage_at_service,
    )
    assert row is not None
    return ServiceHistory.from_row(row)


async def list_history_for_vehicle(db: Db, vehicle_id: uuid.UUID) -> list[ServiceHistory]:
    rows = await db.fetch(
        "SELECT * FROM service_history WHERE vehicle_id = $1 ORDER BY created_at DESC",
        vehicle_id,
    )
    return [ServiceHistory.from_row(r) for r in rows]


async def list_history_for_order(db: Db, order_id: uuid.UUID) -> list[ServiceHistory]:
    rows = await db.fetch(
        "SELECT * FROM service_history WHERE service_order_id = $1 ORDER BY created_at DESC",
        order_id,
    )
    return [ServiceHistory.from_row(r) for r in rows]
