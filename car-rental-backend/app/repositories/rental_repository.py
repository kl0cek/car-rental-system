"""Repozytorium wynajmów (rentals) i rozbicia ceny — czysty SQL (asyncpg).

Tworzenie rekordu przy odbiorze, aktualizacja przy zwrocie oraz listing
per użytkownik z dołączoną rezerwacją (i pojazdem) oraz breakdownem ceny.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.session import Db
from app.models.rental import Rental, RentalPriceBreakdown, Reservation, ReservationStatus
from app.repositories import _relations

SORTABLE_COLUMNS = {
    "pickup_date": "r.pickup_date",
    "return_date": "r.return_date",
    "created_at": "r.created_at",
}


async def _load_reservations(
    db: Db, reservation_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Reservation]:
    if not reservation_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM reservations WHERE id = ANY($1::uuid[])", list(set(reservation_ids))
    )
    reservations = [Reservation.from_row(r) for r in rows]
    vehicles = await _relations.load_vehicles_for(db, [r.vehicle_id for r in reservations])
    for reservation in reservations:
        reservation.vehicle = vehicles.get(reservation.vehicle_id)
    return {r.id: r for r in reservations}


async def _load_breakdowns(
    db: Db, rental_ids: list[uuid.UUID]
) -> dict[uuid.UUID, RentalPriceBreakdown]:
    if not rental_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM rental_price_breakdowns WHERE rental_id = ANY($1::uuid[])",
        list(set(rental_ids)),
    )
    return {r["rental_id"]: RentalPriceBreakdown.from_row(r) for r in rows}


async def _attach(db: Db, rentals: list[Rental]) -> None:
    if not rentals:
        return
    reservations = await _load_reservations(db, [r.reservation_id for r in rentals])
    breakdowns = await _load_breakdowns(db, [r.id for r in rentals])
    for rental in rentals:
        rental.reservation = reservations.get(rental.reservation_id)
        rental.price_breakdown = breakdowns.get(rental.id)


async def get_by_id(db: Db, rental_id: uuid.UUID) -> Rental | None:
    row = await db.fetchrow("SELECT * FROM rentals WHERE id = $1", rental_id)
    if row is None:
        return None
    rental = Rental.from_row(row)
    await _attach(db, [rental])
    return rental


async def get_by_reservation_id(db: Db, reservation_id: uuid.UUID) -> Rental | None:
    row = await db.fetchrow("SELECT * FROM rentals WHERE reservation_id = $1", reservation_id)
    return Rental.from_row(row) if row else None


async def create_pickup(
    db: Db,
    *,
    reservation_id: uuid.UUID,
    employee_id: uuid.UUID,
    mileage_start: int,
    fuel_level_start: Decimal,
    pickup_date: datetime,
) -> Rental:
    row = await db.fetchrow(
        "INSERT INTO rentals (id, reservation_id, employee_id, mileage_start, "
        "fuel_level_start, pickup_date) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
        uuid.uuid4(),
        reservation_id,
        employee_id,
        mileage_start,
        fuel_level_start,
        pickup_date,
    )
    assert row is not None
    return Rental.from_row(row)


async def update_return(
    db: Db,
    rental: Rental,
    *,
    mileage_end: int,
    fuel_level_end: Decimal,
    damage_notes: str | None,
    return_date: datetime,
) -> Rental:
    row = await db.fetchrow(
        "UPDATE rentals SET mileage_end = $2, fuel_level_end = $3, damage_notes = $4, "
        "return_date = $5, updated_at = now() WHERE id = $1 RETURNING *",
        rental.id,
        mileage_end,
        fuel_level_end,
        damage_notes,
        return_date,
    )
    assert row is not None
    updated = Rental.from_row(row)
    # Zachowaj już dociągnięte relacje (np. reservation), jeśli były.
    updated.reservation = rental.reservation
    updated.price_breakdown = rental.price_breakdown
    return updated


async def get_list_by_user(
    db: Db,
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
    conditions = ["res.user_id = $1"]
    args: list[Any] = [user_id]

    def add(template: str, value: Any) -> None:
        args.append(value)
        conditions.append(template.format(n=len(args)))

    if status is not None:
        add("res.status = ${n}", status.value)
    if date_from is not None:
        add("r.pickup_date >= ${n}", date_from)
    if date_to is not None:
        add("r.pickup_date <= ${n}", date_to)

    where = " WHERE " + " AND ".join(conditions)
    from_sql = "FROM rentals r JOIN reservations res ON res.id = r.reservation_id"

    total = await db.fetchval(f"SELECT count(*) {from_sql}{where}", *args)

    sort_col = SORTABLE_COLUMNS.get(sort_by, "r.pickup_date")
    direction = "ASC" if sort_order == "asc" else "DESC"
    nulls = ""
    if sort_by == "return_date":
        nulls = " NULLS LAST" if sort_order == "desc" else " NULLS FIRST"

    rows = await db.fetch(
        f"SELECT r.* {from_sql}{where} ORDER BY {sort_col} {direction}{nulls} "
        f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    rentals = [Rental.from_row(r) for r in rows]
    await _attach(db, rentals)
    return rentals, int(total or 0)


async def create_price_breakdown(
    db: Db,
    *,
    rental_id: uuid.UUID,
    base_price: Decimal,
    risk_multiplier: Decimal,
    final_price: Decimal,
) -> RentalPriceBreakdown:
    row = await db.fetchrow(
        "INSERT INTO rental_price_breakdowns (id, rental_id, base_price, risk_multiplier, "
        "final_price) VALUES ($1, $2, $3, $4, $5) RETURNING *",
        uuid.uuid4(),
        rental_id,
        base_price,
        risk_multiplier,
        final_price,
    )
    assert row is not None
    return RentalPriceBreakdown.from_row(row)
