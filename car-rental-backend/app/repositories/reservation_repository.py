"""Repozytorium rezerwacji — czysty SQL (asyncpg).

Listing per użytkownik, listing admina z filtrami, tworzenie i zmiana
statusu. Pojazd (z kategorią i zdjęciami) oraz użytkownik dociągani są
osobnymi zapytaniami (odpowiednik joinedload/selectinload).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.session import Db
from app.models.rental import Reservation, ReservationStatus
from app.repositories import _relations

SORTABLE_COLUMNS = {
    "created_at": "created_at",
    "start_date": "start_date",
    "end_date": "end_date",
    "total_price": "total_price",
}


async def _attach(db: Db, reservations: list[Reservation], *, with_user: bool) -> None:
    if not reservations:
        return
    vehicles = await _relations.load_vehicles_for(db, [r.vehicle_id for r in reservations])
    for reservation in reservations:
        reservation.vehicle = vehicles.get(reservation.vehicle_id)
    if with_user:
        users = await _relations.load_users_for(db, [r.user_id for r in reservations])
        for reservation in reservations:
            reservation.user = users.get(reservation.user_id)


async def get_by_id(db: Db, reservation_id: uuid.UUID) -> Reservation | None:
    row = await db.fetchrow("SELECT * FROM reservations WHERE id = $1", reservation_id)
    if row is None:
        return None
    reservation = Reservation.from_row(row)
    await _attach(db, [reservation], with_user=True)
    return reservation


async def get_by_id_for_update(db: Db, reservation_id: uuid.UUID) -> Reservation | None:
    """Zablokuj wiersz rezerwacji (FOR UPDATE), potem zwróć z relacjami.

    Blokadę i eager-load rozdzielamy — FOR UPDATE nie może działać na
    nullowalnej stronie outer-joina (relacje ładujemy osobnymi zapytaniami).
    """
    await db.execute("SELECT id FROM reservations WHERE id = $1 FOR UPDATE", reservation_id)
    return await get_by_id(db, reservation_id)


async def get_list_by_user(
    db: Db,
    user_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 20,
    status: ReservationStatus | None = None,
) -> tuple[list[Reservation], int]:
    conditions = ["user_id = $1"]
    args: list[Any] = [user_id]
    if status is not None:
        args.append(status.value)
        conditions.append(f"status = ${len(args)}")
    where = " WHERE " + " AND ".join(conditions)

    total = await db.fetchval(f"SELECT count(*) FROM reservations{where}", *args)

    rows = await db.fetch(
        f"SELECT * FROM reservations{where} ORDER BY created_at DESC "
        f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    reservations = [Reservation.from_row(r) for r in rows]
    await _attach(db, reservations, with_user=False)
    return reservations, int(total or 0)


async def get_admin_list(
    db: Db,
    *,
    offset: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    status: ReservationStatus | None = None,
    user_id: uuid.UUID | None = None,
    vehicle_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[Reservation], int]:
    conditions: list[str] = []
    args: list[Any] = []

    def add(template: str, value: Any) -> None:
        args.append(value)
        conditions.append(template.format(n=len(args)))

    if status is not None:
        add("status = ${n}", status.value)
    if user_id is not None:
        add("user_id = ${n}", user_id)
    if vehicle_id is not None:
        add("vehicle_id = ${n}", vehicle_id)
    # Semantyka nakładania: rezerwacje przecinające [date_from, date_to].
    if date_from is not None:
        add("end_date >= ${n}", date_from)
    if date_to is not None:
        add("start_date <= ${n}", date_to)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total = await db.fetchval(f"SELECT count(*) FROM reservations{where}", *args)

    sort_col = SORTABLE_COLUMNS.get(sort_by, "created_at")
    direction = "ASC" if sort_order == "asc" else "DESC"

    rows = await db.fetch(
        f"SELECT * FROM reservations{where} ORDER BY {sort_col} {direction} "
        f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    reservations = [Reservation.from_row(r) for r in rows]
    await _attach(db, reservations, with_user=True)
    return reservations, int(total or 0)


async def create(
    db: Db,
    *,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
    total_price: Decimal,
) -> Reservation:
    row = await db.fetchrow(
        "INSERT INTO reservations (id, user_id, vehicle_id, start_date, end_date, status, "
        "total_price) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *",
        uuid.uuid4(),
        user_id,
        vehicle_id,
        start_date,
        end_date,
        ReservationStatus.PENDING.value,
        total_price,
    )
    assert row is not None
    reservation = Reservation.from_row(row)
    await _attach(db, [reservation], with_user=False)
    return reservation


async def update_status(
    db: Db,
    reservation: Reservation,
    new_status: ReservationStatus,
) -> Reservation:
    await db.execute(
        "UPDATE reservations SET status = $2, updated_at = now() WHERE id = $1",
        reservation.id,
        new_status.value,
    )
    reservation.status = new_status
    return reservation
