"""Repozytorium pojazdów — czysty SQL (asyncpg).

Katalog z filtrami, sprawdzanie kolizji rezerwacji w przedziale dat,
CRUD oraz utrzymanie niezmiennika "dokładnie jedno zdjęcie podstawowe na
pojazd". Relacje (kategoria, zdjęcia) dociągane są pomocnikami z
``_relations`` (odpowiednik selectinload).
"""

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from app.core.utils import date_to_utc_datetime
from app.db.session import Db
from app.models.category import CategoryName
from app.models.rental import ReservationStatus
from app.models.vehicle import EngineType, Vehicle, VehicleStatus
from app.models.vehicle_image import VehicleImage
from app.repositories import _relations

# Whitelist kolumn ORDER BY (sort_by pochodzi z zewnątrz — nie wolno wstrzyknąć).
SORTABLE_COLUMNS = {
    "brand": "v.brand",
    "model": "v.model",
    "year": "v.year",
    "daily_base_price": "v.daily_base_price",
    "created_at": "v.created_at",
    "mileage": "v.mileage",
    "horsepower": "v.horsepower",
}

BLOCKING_STATUSES = [
    ReservationStatus.PENDING.value,
    ReservationStatus.CONFIRMED.value,
    ReservationStatus.ACTIVE.value,
]


def _date_to_datetime_end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=UTC)


class _Filters:
    """Buduje fragment WHERE i listę parametrów dla katalogu pojazdów."""

    def __init__(self) -> None:
        self.conditions: list[str] = ["v.is_active = true"]
        self.args: list[Any] = []
        self.joins_category = False

    def add(self, template: str, value: Any) -> None:
        self.args.append(value)
        self.conditions.append(template.format(n=len(self.args)))

    def apply(
        self,
        *,
        category: CategoryName | None,
        engine_type: EngineType | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        min_year: int | None,
        max_year: int | None,
        min_seats: int | None,
        status: VehicleStatus | None,
        status_in: list[VehicleStatus] | None,
        search: str | None,
    ) -> None:
        if category is not None:
            self.joins_category = True
            self.add("c.name = ${n}", category.value)
        if engine_type is not None:
            self.add("v.engine_type = ${n}", engine_type.value)
        if min_price is not None:
            self.add("v.daily_base_price >= ${n}", min_price)
        if max_price is not None:
            self.add("v.daily_base_price <= ${n}", max_price)
        if min_year is not None:
            self.add("v.year >= ${n}", min_year)
        if max_year is not None:
            self.add("v.year <= ${n}", max_year)
        if min_seats is not None:
            self.add("v.seats >= ${n}", min_seats)
        if status is not None:
            self.add("v.status = ${n}", status.value)
        if status_in is not None:
            self.add("v.status = ANY(${n}::text[])", [s.value for s in status_in])
        if search:
            like = f"%{search.strip()}%"
            self.args.append(like)
            n = len(self.args)
            self.conditions.append(
                f"(v.brand ILIKE ${n} OR v.model ILIKE ${n} "
                f"OR v.license_plate ILIKE ${n} OR v.vin ILIKE ${n})"
            )

    def from_clause(self) -> str:
        if self.joins_category:
            return "FROM vehicles v JOIN categories c ON c.id = v.category_id"
        return "FROM vehicles v"

    def where_clause(self) -> str:
        return " WHERE " + " AND ".join(self.conditions)


async def get_list(
    db: Db,
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
    f = _Filters()
    f.apply(
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
        # Wyklucz pojazdy z kolidującą rezerwacją (nakładające się przedziały).
        f.args.append(BLOCKING_STATUSES)
        i_status = len(f.args)
        f.args.append(_date_to_datetime_end(available_to))
        i_to = len(f.args)
        f.args.append(date_to_utc_datetime(available_from))
        i_from = len(f.args)
        f.conditions.append(
            f"v.id NOT IN (SELECT vehicle_id FROM reservations "
            f"WHERE status = ANY(${i_status}::text[]) "
            f"AND start_date < ${i_to} AND end_date > ${i_from})"
        )

    from_sql = f.from_clause()
    where_sql = f.where_clause()

    total = await db.fetchval(f"SELECT count(*) {from_sql}{where_sql}", *f.args)

    sort_col = SORTABLE_COLUMNS.get(sort_by, "v.created_at")
    direction = "ASC" if sort_order == "asc" else "DESC"

    rows = await db.fetch(
        f"SELECT v.* {from_sql}{where_sql} ORDER BY {sort_col} {direction} "
        f"LIMIT ${len(f.args) + 1} OFFSET ${len(f.args) + 2}",
        *f.args,
        limit,
        offset,
    )
    vehicles = [Vehicle.from_row(r) for r in rows]
    await _relations.attach_vehicle_relations(db, vehicles)
    return vehicles, int(total or 0)


async def get_by_id(db: Db, vehicle_id: uuid.UUID) -> Vehicle | None:
    row = await db.fetchrow("SELECT * FROM vehicles WHERE id = $1 AND is_active = true", vehicle_id)
    if row is None:
        return None
    vehicle = Vehicle.from_row(row)
    await _relations.attach_vehicle_relations(db, [vehicle])
    return vehicle


async def get_by_id_for_update(db: Db, vehicle_id: uuid.UUID) -> Vehicle | None:
    """Zablokuj wiersz pojazdu (FOR UPDATE), potem zwróć z relacjami.

    Blokadę i dociągnięcie relacji rozdzielamy — FOR UPDATE nie może działać
    na nullowalnej stronie outer-joina (relacje ładujemy osobnymi zapytaniami).
    """
    await db.execute("SELECT id FROM vehicles WHERE id = $1 FOR UPDATE", vehicle_id)
    return await get_by_id(db, vehicle_id)


async def count_conflicting_reservations(
    db: Db,
    vehicle_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> int:
    # Rezerwacje kolidują gdy: A.start < B.end AND A.end > B.start.
    total = await db.fetchval(
        "SELECT count(*) FROM reservations "
        "WHERE vehicle_id = $1 AND status = ANY($2::text[]) "
        "AND start_date < $3 AND end_date > $4",
        vehicle_id,
        BLOCKING_STATUSES,
        _date_to_datetime_end(end_date),
        date_to_utc_datetime(start_date),
    )
    return int(total or 0)


async def has_blocking_reservations(db: Db, vehicle_id: uuid.UUID) -> bool:
    """True, jeśli pojazd ma jakąkolwiek rezerwację pending/confirmed/active."""
    row = await db.fetchrow(
        "SELECT 1 FROM reservations WHERE vehicle_id = $1 AND status = ANY($2::text[]) LIMIT 1",
        vehicle_id,
        BLOCKING_STATUSES,
    )
    return row is not None


async def create(db: Db, vehicle: Vehicle) -> Vehicle:
    row = await db.fetchrow(
        "INSERT INTO vehicles (id, brand, model, year, license_plate, vin, engine_type, "
        "horsepower, seats, trunk_capacity, daily_base_price, color, mileage, status, "
        "is_active, avg_rating, ratings_count, category_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18) "
        "RETURNING *",
        vehicle.id,
        vehicle.brand,
        vehicle.model,
        vehicle.year,
        vehicle.license_plate,
        vehicle.vin,
        vehicle.engine_type.value,
        vehicle.horsepower,
        vehicle.seats,
        vehicle.trunk_capacity,
        vehicle.daily_base_price,
        vehicle.color.value,
        vehicle.mileage,
        vehicle.status.value,
        vehicle.is_active,
        vehicle.avg_rating,
        vehicle.ratings_count,
        vehicle.category_id,
    )
    assert row is not None
    created = Vehicle.from_row(row)
    await _relations.attach_vehicle_relations(db, [created])
    return created


async def update(db: Db, vehicle: Vehicle) -> Vehicle:
    # avg_rating / ratings_count celowo pomijamy — utrzymuje je wyłącznie
    # review_service, by edycja pojazdu nie nadpisała współbieżnej zmiany ocen.
    row = await db.fetchrow(
        "UPDATE vehicles SET brand = $2, model = $3, year = $4, license_plate = $5, vin = $6, "
        "engine_type = $7, horsepower = $8, seats = $9, trunk_capacity = $10, "
        "daily_base_price = $11, color = $12, mileage = $13, status = $14, is_active = $15, "
        "category_id = $16, updated_at = now() WHERE id = $1 RETURNING *",
        vehicle.id,
        vehicle.brand,
        vehicle.model,
        vehicle.year,
        vehicle.license_plate,
        vehicle.vin,
        vehicle.engine_type.value,
        vehicle.horsepower,
        vehicle.seats,
        vehicle.trunk_capacity,
        vehicle.daily_base_price,
        vehicle.color.value,
        vehicle.mileage,
        vehicle.status.value,
        vehicle.is_active,
        vehicle.category_id,
    )
    assert row is not None
    updated = Vehicle.from_row(row)
    await _relations.attach_vehicle_relations(db, [updated])
    return updated


async def soft_delete(db: Db, vehicle: Vehicle) -> Vehicle:
    await db.execute(
        "UPDATE vehicles SET is_active = false, updated_at = now() WHERE id = $1", vehicle.id
    )
    vehicle.is_active = False
    return vehicle


async def bulk_update_status(
    db: Db,
    ids: list[uuid.UUID],
    status: VehicleStatus,
) -> tuple[int, list[uuid.UUID]]:
    """Zmień status wielu pojazdów jednym zapytaniem.

    Zwraca ``(liczba_zaktualizowanych, brakujące_id)`` — brakujące to id, które
    nie istnieją lub są soft-deleted (caller pokazuje je jako częściowy sukces).
    """
    if not ids:
        return 0, []

    existing_rows = await db.fetch(
        "SELECT id FROM vehicles WHERE id = ANY($1::uuid[]) AND is_active = true", ids
    )
    existing = {r["id"] for r in existing_rows}
    missing = [vid for vid in ids if vid not in existing]

    if not existing:
        return 0, missing

    await db.execute(
        "UPDATE vehicles SET status = $2, updated_at = now() "
        "WHERE id = ANY($1::uuid[]) AND is_active = true",
        list(existing),
        status.value,
    )
    return len(existing), missing


async def _lock_vehicle_row(db: Db, vehicle_id: uuid.UUID) -> None:
    """Załóż blokadę FOR UPDATE na wierszu pojazdu (serializacja zmian zdjęć)."""
    await db.execute("SELECT id FROM vehicles WHERE id = $1 FOR UPDATE", vehicle_id)


async def add_image(db: Db, vehicle_id: uuid.UUID, url: str, is_primary: bool) -> VehicleImage:
    await _lock_vehicle_row(db, vehicle_id)
    next_position = await db.fetchval(
        "SELECT coalesce(max(position) + 1, 0) FROM vehicle_images WHERE vehicle_id = $1",
        vehicle_id,
    )
    if is_primary:
        # Zdejmij flagę z poprzedniego primary — inaczej częściowy indeks da 23505.
        await db.execute(
            "UPDATE vehicle_images SET is_primary = false, updated_at = now() "
            "WHERE vehicle_id = $1 AND is_primary = true",
            vehicle_id,
        )
    row = await db.fetchrow(
        "INSERT INTO vehicle_images (id, vehicle_id, url, position, is_primary) "
        "VALUES ($1, $2, $3, $4, $5) RETURNING *",
        uuid.uuid4(),
        vehicle_id,
        url,
        int(next_position or 0),
        is_primary,
    )
    assert row is not None
    return VehicleImage.from_row(row)


async def get_image(db: Db, image_id: uuid.UUID) -> VehicleImage | None:
    row = await db.fetchrow("SELECT * FROM vehicle_images WHERE id = $1", image_id)
    return VehicleImage.from_row(row) if row else None


async def delete_image(db: Db, image: VehicleImage) -> None:
    await _lock_vehicle_row(db, image.vehicle_id)
    await db.execute("DELETE FROM vehicle_images WHERE id = $1", image.id)

    # Jeśli usunięto primary — awansuj zdjęcie o najniższym position.
    if image.is_primary:
        row = await db.fetchrow(
            "SELECT id FROM vehicle_images WHERE vehicle_id = $1 ORDER BY position LIMIT 1",
            image.vehicle_id,
        )
        if row is not None:
            await db.execute(
                "UPDATE vehicle_images SET is_primary = true, updated_at = now() WHERE id = $1",
                row["id"],
            )


async def set_primary_image(db: Db, image: VehicleImage) -> None:
    if image.is_primary:
        return
    await _lock_vehicle_row(db, image.vehicle_id)
    await db.execute(
        "UPDATE vehicle_images SET is_primary = false, updated_at = now() "
        "WHERE vehicle_id = $1 AND is_primary = true",
        image.vehicle_id,
    )
    await db.execute(
        "UPDATE vehicle_images SET is_primary = true, updated_at = now() WHERE id = $1",
        image.id,
    )
    image.is_primary = True


async def reorder_images(
    db: Db,
    vehicle_id: uuid.UUID,
    ordered_ids: list[uuid.UUID],
) -> list[VehicleImage]:
    """Nadaj nowy ``position`` każdemu zdjęciu w podanej kolejności.

    Id nienależące do pojazdu są pomijane (gwarancja przez WHERE vehicle_id).
    """
    for index, img_id in enumerate(ordered_ids):
        await db.execute(
            "UPDATE vehicle_images SET position = $2, updated_at = now() "
            "WHERE id = $1 AND vehicle_id = $3",
            img_id,
            index,
            vehicle_id,
        )
    rows = await db.fetch(
        "SELECT * FROM vehicle_images WHERE vehicle_id = $1 ORDER BY position", vehicle_id
    )
    return [VehicleImage.from_row(r) for r in rows]


async def get_booked_dates(db: Db, vehicle_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = await db.fetch(
        "SELECT start_date, end_date FROM reservations "
        "WHERE vehicle_id = $1 AND status = ANY($2::text[]) AND end_date > now() "
        "ORDER BY start_date",
        vehicle_id,
        BLOCKING_STATUSES,
    )
    return [{"start_date": r["start_date"], "end_date": r["end_date"]} for r in rows]
