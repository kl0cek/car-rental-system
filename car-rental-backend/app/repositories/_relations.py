"""Wspólne pomocniki do dociągania relacji (odpowiednik ``selectinload``).

Zamiast łączyć tabele w jednym zapytaniu (co przy ORM robił joinedload),
ładujemy encje powiązane partią — jednym ``SELECT ... WHERE id = ANY($1)``
— i zszywamy je w Pythonie. Dzięki temu unikamy kolizji nazw kolumn przy
JOIN-ach i zachowujemy natywne typy asyncpg (UUID, Decimal, timestamptz).
"""

import uuid

from app.db.session import Db
from app.models.category import Category
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicle_image import VehicleImage


async def load_images_for(
    db: Db, vehicle_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[VehicleImage]]:
    """Zwróć mapę vehicle_id -> lista zdjęć (posortowanych po position)."""
    if not vehicle_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM vehicle_images WHERE vehicle_id = ANY($1::uuid[]) ORDER BY position",
        list(set(vehicle_ids)),
    )
    result: dict[uuid.UUID, list[VehicleImage]] = {}
    for row in rows:
        result.setdefault(row["vehicle_id"], []).append(VehicleImage.from_row(row))
    return result


async def load_categories_for(db: Db, category_ids: list[uuid.UUID]) -> dict[uuid.UUID, Category]:
    if not category_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM categories WHERE id = ANY($1::uuid[])", list(set(category_ids))
    )
    return {row["id"]: Category.from_row(row) for row in rows}


async def load_users_for(db: Db, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
    if not user_ids:
        return {}
    rows = await db.fetch("SELECT * FROM users WHERE id = ANY($1::uuid[])", list(set(user_ids)))
    return {row["id"]: User.from_row(row) for row in rows}


async def attach_vehicle_relations(db: Db, vehicles: list[Vehicle]) -> None:
    """Wypełnij ``vehicle.category`` i ``vehicle.images`` dla listy pojazdów."""
    if not vehicles:
        return
    categories = await load_categories_for(db, [v.category_id for v in vehicles])
    images = await load_images_for(db, [v.id for v in vehicles])
    for vehicle in vehicles:
        vehicle.category = categories.get(vehicle.category_id)
        vehicle.images = images.get(vehicle.id, [])


async def load_vehicles_for(db: Db, vehicle_ids: list[uuid.UUID]) -> dict[uuid.UUID, Vehicle]:
    """Załaduj pojazdy po id (z kategorią i zdjęciami) — bez filtra is_active.

    Używane przy zszywaniu relacji rezerwacji/wynajmu, gdzie pojazd mógł zostać
    soft-deleted, a historyczny rekord nadal musi się wyświetlić.
    """
    if not vehicle_ids:
        return {}
    rows = await db.fetch(
        "SELECT * FROM vehicles WHERE id = ANY($1::uuid[])", list(set(vehicle_ids))
    )
    vehicles = [Vehicle.from_row(r) for r in rows]
    await attach_vehicle_relations(db, vehicles)
    return {v.id: v for v in vehicles}
