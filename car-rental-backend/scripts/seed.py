"""
Seed script for DriveEase — populates PostgreSQL, MongoDB, and Redis with example data.

Usage:
    cd car-rental-backend
    python -m scripts.seed          # seed all databases
    python -m scripts.seed --pg     # seed PostgreSQL only
    python -m scripts.seed --mongo  # seed MongoDB only
    python -m scripts.seed --redis  # seed Redis only
    python -m scripts.seed --drop   # drop existing data before seeding
"""

import argparse
import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

# ---------------------------------------------------------------------------
# Shared IDs (so we can reference them across databases)
# ---------------------------------------------------------------------------
USER_IDS = [uuid.uuid4() for _ in range(6)]
CATEGORY_IDS = [uuid.uuid4() for _ in range(5)]
VEHICLE_IDS = [uuid.uuid4() for _ in range(8)]
RENTAL_IDS = [uuid.uuid4() for _ in range(10)]

NOW = datetime.now(UTC)


# ===========================================================================
# PostgreSQL seed
# ===========================================================================
async def seed_postgres(*, drop: bool = False) -> None:
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.db.base import Base
    from app.db.engine import async_engine, async_session_factory
    from app.models.category import Category, CategoryName
    from app.models.rental import Rental, RentalStatus
    from app.models.user import User, UserRole
    from app.models.vehicle import EngineType, Vehicle, VehicleStatus

    if drop:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("[PG] Dropped all tables")

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[PG] Tables created")

    # --- Users ---
    # All seed users have the password "Password1" for testing
    seed_password = hash_password("Password1")

    users = [
        User(
            id=USER_IDS[0],
            email="jan.kowalski@example.com",
            hashed_password=seed_password,
            first_name="Jan",
            last_name="Kowalski",
            role=UserRole.CUSTOMER,
            phone="+48600100200",
            is_verified=True,
        ),
        User(
            id=USER_IDS[1],
            email="anna.nowak@example.com",
            hashed_password=seed_password,
            first_name="Anna",
            last_name="Nowak",
            role=UserRole.CUSTOMER,
            phone="+48601200300",
            is_verified=True,
        ),
        User(
            id=USER_IDS[2],
            email="piotr.wisniewski@example.com",
            hashed_password=seed_password,
            first_name="Piotr",
            last_name="Wiśniewski",
            role=UserRole.CUSTOMER,
            is_verified=True,
        ),
        User(
            id=USER_IDS[3],
            email="employee@driveease.com",
            hashed_password=seed_password,
            first_name="Marta",
            last_name="Zielińska",
            role=UserRole.EMPLOYEE,
            phone="+48602300400",
            is_verified=True,
        ),
        User(
            id=USER_IDS[4],
            email="technician@driveease.com",
            hashed_password=seed_password,
            first_name="Tomasz",
            last_name="Lewandowski",
            role=UserRole.TECHNICIAN,
            phone="+48603400500",
            is_verified=True,
        ),
        User(
            id=USER_IDS[5],
            email="admin@driveease.com",
            hashed_password=seed_password,
            first_name="Katarzyna",
            last_name="Wójcik",
            role=UserRole.ADMIN,
            phone="+48604500600",
            is_verified=True,
        ),
    ]

    # --- Categories ---
    categories = [
        Category(
            id=CATEGORY_IDS[0],
            name=CategoryName.ECONOMY,
            description="Tanie, oszczędne samochody na co dzień",
            price_multiplier=Decimal("1.000"),
        ),
        Category(
            id=CATEGORY_IDS[1],
            name=CategoryName.COMFORT,
            description="Wygodne samochody klasy średniej",
            price_multiplier=Decimal("1.200"),
        ),
        Category(
            id=CATEGORY_IDS[2],
            name=CategoryName.PREMIUM,
            description="Samochody klasy premium i luksusowe",
            price_multiplier=Decimal("1.600"),
        ),
        Category(
            id=CATEGORY_IDS[3],
            name=CategoryName.SUV,
            description="SUV-y i crossovery",
            price_multiplier=Decimal("1.400"),
        ),
        Category(
            id=CATEGORY_IDS[4],
            name=CategoryName.VAN,
            description="Vany i samochody wieloosobowe",
            price_multiplier=Decimal("1.300"),
        ),
    ]

    # --- Vehicles (VINs are fabricated for seeding; not check-digit valid) ---
    vehicles = [
        Vehicle(
            id=VEHICLE_IDS[0],
            brand="Toyota",
            model="Corolla",
            year=2023,
            license_plate="WA 12345",
            vin="JTDKN3DU5A0000001",
            engine_type=EngineType.PETROL,
            horsepower=140,
            seats=5,
            trunk_capacity=361,
            daily_base_price=Decimal("150.00"),
            color="Biały",
            mileage=25000,
            status=VehicleStatus.AVAILABLE,
            category_id=CATEGORY_IDS[1],
        ),
        Vehicle(
            id=VEHICLE_IDS[1],
            brand="Volkswagen",
            model="Golf",
            year=2022,
            license_plate="KR 67890",
            vin="WVWZZZ1KZAW000002",
            engine_type=EngineType.DIESEL,
            horsepower=150,
            seats=5,
            trunk_capacity=381,
            daily_base_price=Decimal("170.00"),
            color="Szary",
            mileage=45000,
            status=VehicleStatus.RENTED,
            category_id=CATEGORY_IDS[1],
        ),
        Vehicle(
            id=VEHICLE_IDS[2],
            brand="Tesla",
            model="Model 3",
            year=2024,
            license_plate="GD 11111",
            vin="5YJ3E1EA1PF000003",
            engine_type=EngineType.ELECTRIC,
            horsepower=283,
            seats=5,
            trunk_capacity=425,
            daily_base_price=Decimal("350.00"),
            color="Czarny",
            mileage=8000,
            status=VehicleStatus.AVAILABLE,
            category_id=CATEGORY_IDS[2],
        ),
        Vehicle(
            id=VEHICLE_IDS[3],
            brand="Toyota",
            model="RAV4 Hybrid",
            year=2023,
            license_plate="PO 22222",
            vin="JTMRWRFV5MD000004",
            engine_type=EngineType.HYBRID,
            horsepower=222,
            seats=5,
            trunk_capacity=580,
            daily_base_price=Decimal("280.00"),
            color="Zielony",
            mileage=18000,
            status=VehicleStatus.AVAILABLE,
            category_id=CATEGORY_IDS[3],
        ),
        Vehicle(
            id=VEHICLE_IDS[4],
            brand="Skoda",
            model="Octavia",
            year=2021,
            license_plate="DWR 33333",
            vin="TMBAG7NE1M0000005",
            engine_type=EngineType.DIESEL,
            horsepower=150,
            seats=5,
            trunk_capacity=600,
            daily_base_price=Decimal("140.00"),
            color="Niebieski",
            mileage=72000,
            status=VehicleStatus.MAINTENANCE,
            category_id=CATEGORY_IDS[1],
        ),
        Vehicle(
            id=VEHICLE_IDS[5],
            brand="BMW",
            model="320i",
            year=2024,
            license_plate="KA 44444",
            vin="WBA5R1C50KA000006",
            engine_type=EngineType.PETROL,
            horsepower=184,
            seats=5,
            trunk_capacity=480,
            daily_base_price=Decimal("320.00"),
            color="Czarny",
            mileage=5000,
            status=VehicleStatus.AVAILABLE,
            category_id=CATEGORY_IDS[2],
        ),
        Vehicle(
            id=VEHICLE_IDS[6],
            brand="Hyundai",
            model="Kona Electric",
            year=2023,
            license_plate="LU 55555",
            vin="KMHK381GFLU000007",
            engine_type=EngineType.ELECTRIC,
            horsepower=204,
            seats=5,
            trunk_capacity=332,
            daily_base_price=Decimal("250.00"),
            color="Biały",
            mileage=12000,
            status=VehicleStatus.AVAILABLE,
            category_id=CATEGORY_IDS[1],
        ),
        Vehicle(
            id=VEHICLE_IDS[7],
            brand="Ford",
            model="Focus",
            year=2020,
            license_plate="SZ 66666",
            vin="WF0XXXGCDXKY00008",
            engine_type=EngineType.PETROL,
            horsepower=125,
            seats=5,
            trunk_capacity=375,
            daily_base_price=Decimal("120.00"),
            color="Czerwony",
            mileage=95000,
            status=VehicleStatus.OUT_OF_SERVICE,
            category_id=CATEGORY_IDS[0],
        ),
    ]

    # --- Rentals ---
    rentals = [
        Rental(
            id=RENTAL_IDS[0],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=30),
            end_date=NOW - timedelta(days=25),
            total_price=750.00,
            status=RentalStatus.COMPLETED,
        ),
        Rental(
            id=RENTAL_IDS[1],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[2],
            start_date=NOW - timedelta(days=15),
            end_date=NOW - timedelta(days=12),
            total_price=1050.00,
            status=RentalStatus.COMPLETED,
        ),
        Rental(
            id=RENTAL_IDS[2],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[1],
            start_date=NOW - timedelta(days=3),
            end_date=NOW + timedelta(days=4),
            total_price=1190.00,
            status=RentalStatus.ACTIVE,
        ),
        Rental(
            id=RENTAL_IDS[3],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[3],
            start_date=NOW - timedelta(days=60),
            end_date=NOW - timedelta(days=55),
            total_price=1400.00,
            status=RentalStatus.COMPLETED,
        ),
        Rental(
            id=RENTAL_IDS[4],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[5],
            start_date=NOW + timedelta(days=2),
            end_date=NOW + timedelta(days=5),
            total_price=960.00,
            status=RentalStatus.PENDING,
        ),
        Rental(
            id=RENTAL_IDS[5],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=90),
            end_date=NOW - timedelta(days=85),
            total_price=750.00,
            status=RentalStatus.COMPLETED,
        ),
        Rental(
            id=RENTAL_IDS[6],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[6],
            start_date=NOW + timedelta(days=7),
            end_date=NOW + timedelta(days=14),
            total_price=1750.00,
            status=RentalStatus.PENDING,
            notes="Potrzebna ładowarka domowa",
        ),
        Rental(
            id=RENTAL_IDS[7],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=120),
            end_date=NOW - timedelta(days=117),
            total_price=450.00,
            status=RentalStatus.COMPLETED,
        ),
        Rental(
            id=RENTAL_IDS[8],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[3],
            start_date=NOW - timedelta(days=45),
            end_date=NOW - timedelta(days=44),
            total_price=280.00,
            status=RentalStatus.CANCELLED,
            notes="Klient odwołał rezerwację",
        ),
        Rental(
            id=RENTAL_IDS[9],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[4],
            start_date=NOW - timedelta(days=200),
            end_date=NOW - timedelta(days=193),
            total_price=980.00,
            status=RentalStatus.COMPLETED,
        ),
    ]

    async with async_session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT count(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print(f"[PG] Skipping — {count} users already exist (use --drop to reset)")
            return

        session.add_all(users)
        await session.flush()
        session.add_all(categories)
        await session.flush()
        session.add_all(vehicles)
        await session.flush()
        session.add_all(rentals)
        await session.commit()

    print(
        f"[PG] Seeded: {len(users)} users, {len(categories)} categories, "
        f"{len(vehicles)} vehicles, {len(rentals)} rentals"
    )

    await async_engine.dispose()


# ===========================================================================
# MongoDB seed
# ===========================================================================
async def seed_mongo(*, drop: bool = False) -> None:
    from app.db.mongodb import connect_mongo, get_mongo_db

    await connect_mongo()
    mongo_db = get_mongo_db()

    if drop:
        for coll_name in [
            "rental_logs",
            "reviews",
            "price_history",
            "incidents",
            "user_preferences",
        ]:
            await mongo_db.drop_collection(coll_name)
        print("[MONGO] Dropped all collections")

    # --- Rental logs (analytics) ---
    existing = await mongo_db.rental_logs.count_documents({})
    if existing > 0:
        print(f"[MONGO] Skipping — {existing} rental logs already exist")
        return

    rental_logs = [
        {
            "rental_id": str(RENTAL_IDS[0]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=30)).isoformat(),
            "mileage_at_event": 24500,
            "location": "Warszawa - oddział główny",
        },
        {
            "rental_id": str(RENTAL_IDS[0]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "action": "return",
            "timestamp": (NOW - timedelta(days=25)).isoformat(),
            "mileage_at_event": 25000,
            "location": "Warszawa - oddział główny",
            "fuel_level": 0.75,
        },
        {
            "rental_id": str(RENTAL_IDS[2]),
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[1]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=3)).isoformat(),
            "mileage_at_event": 44800,
            "location": "Kraków - lotnisko",
        },
        {
            "rental_id": str(RENTAL_IDS[1]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=15)).isoformat(),
            "mileage_at_event": 7500,
            "location": "Gdańsk - centrum",
        },
        {
            "rental_id": str(RENTAL_IDS[1]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "action": "return",
            "timestamp": (NOW - timedelta(days=12)).isoformat(),
            "mileage_at_event": 8000,
            "location": "Gdańsk - centrum",
            "battery_level": 0.45,
        },
    ]

    # --- Reviews ---
    reviews = [
        {
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "rental_id": str(RENTAL_IDS[0]),
            "rating": 5,
            "comment": "Świetny samochód, czysty i zadbany. Polecam!",
            "created_at": (NOW - timedelta(days=24)).isoformat(),
        },
        {
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "rental_id": str(RENTAL_IDS[1]),
            "rating": 4,
            "comment": "Tesla super, ale zasięg mniejszy niż obiecany.",
            "created_at": (NOW - timedelta(days=11)).isoformat(),
        },
        {
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[3]),
            "rental_id": str(RENTAL_IDS[3]),
            "rating": 5,
            "comment": "RAV4 Hybrid idealny na dłuższą trasę. Niskie spalanie.",
            "created_at": (NOW - timedelta(days=54)).isoformat(),
        },
        {
            "user_id": str(USER_IDS[2]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "rental_id": str(RENTAL_IDS[5]),
            "rating": 3,
            "comment": "Samochód OK, ale trochę hałaśliwy silnik.",
            "created_at": (NOW - timedelta(days=84)).isoformat(),
        },
    ]

    # --- Price history ---
    price_history = []
    for days_ago in [90, 60, 30, 14, 7, 1]:
        price_history.append(
            {
                "fuel_type": "petrol_95",
                "price_per_liter": round(6.20 + (90 - days_ago) * 0.005, 2),
                "currency": "PLN",
                "source": "e-petrol.pl",
                "recorded_at": (NOW - timedelta(days=days_ago)).isoformat(),
            }
        )
        price_history.append(
            {
                "fuel_type": "diesel",
                "price_per_liter": round(6.50 + (90 - days_ago) * 0.004, 2),
                "currency": "PLN",
                "source": "e-petrol.pl",
                "recorded_at": (NOW - timedelta(days=days_ago)).isoformat(),
            }
        )
        price_history.append(
            {
                "fuel_type": "electricity_kwh",
                "price_per_liter": round(0.85 + (90 - days_ago) * 0.001, 2),
                "currency": "PLN",
                "source": "URE",
                "recorded_at": (NOW - timedelta(days=days_ago)).isoformat(),
            }
        )

    # --- Incidents ---
    incidents = [
        {
            "rental_id": str(RENTAL_IDS[9]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[4]),
            "type": "minor_damage",
            "description": "Drobne zarysowanie zderzaka przedniego na parkingu.",
            "severity": "low",
            "reported_at": (NOW - timedelta(days=195)).isoformat(),
            "resolved": True,
            "repair_cost": 450.00,
        },
        {
            "rental_id": str(RENTAL_IDS[3]),
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[3]),
            "type": "flat_tire",
            "description": "Przebita opona na autostradzie A4. Wymieniono na zapasową.",
            "severity": "medium",
            "reported_at": (NOW - timedelta(days=57)).isoformat(),
            "resolved": True,
            "repair_cost": 320.00,
        },
    ]

    # --- User UI preferences ---
    user_preferences = [
        {
            "user_id": str(USER_IDS[0]),
            "theme": "dark",
            "language": "pl",
            "notifications_enabled": True,
            "default_sort": "price_asc",
        },
        {
            "user_id": str(USER_IDS[1]),
            "theme": "light",
            "language": "pl",
            "notifications_enabled": True,
            "default_sort": "brand_asc",
        },
        {
            "user_id": str(USER_IDS[2]),
            "theme": "dark",
            "language": "en",
            "notifications_enabled": False,
            "default_sort": "newest",
        },
    ]

    await mongo_db.rental_logs.insert_many(rental_logs)
    await mongo_db.reviews.insert_many(reviews)
    await mongo_db.price_history.insert_many(price_history)
    await mongo_db.incidents.insert_many(incidents)
    await mongo_db.user_preferences.insert_many(user_preferences)

    # Create indexes
    await mongo_db.rental_logs.create_index("rental_id")
    await mongo_db.rental_logs.create_index("user_id")
    await mongo_db.reviews.create_index("vehicle_id")
    await mongo_db.reviews.create_index("user_id")
    await mongo_db.price_history.create_index([("fuel_type", 1), ("recorded_at", -1)])
    await mongo_db.incidents.create_index("rental_id")
    await mongo_db.user_preferences.create_index("user_id", unique=True)

    print(
        f"[MONGO] Seeded: {len(rental_logs)} logs, {len(reviews)} reviews, "
        f"{len(price_history)} price records, {len(incidents)} incidents, "
        f"{len(user_preferences)} user preferences"
    )


# ===========================================================================
# Redis seed
# ===========================================================================
async def seed_redis(*, drop: bool = False) -> None:
    from app.db.redis import connect_redis, get_redis

    await connect_redis()
    redis_client = get_redis()

    if drop:
        await redis_client.flushdb()
        print("[REDIS] Flushed database")

    existing = await redis_client.dbsize()
    if existing and existing > 0:
        print(f"[REDIS] Skipping — {existing} keys already exist (use --drop to reset)")
        return

    # --- Vehicle availability cache ---
    for i, vid in enumerate(VEHICLE_IDS):
        statuses = [
            "available",
            "rented",
            "available",
            "available",
            "maintenance",
            "available",
            "available",
            "out_of_service",
        ]
        await redis_client.setex(
            f"vehicle:availability:{vid}",
            3600,
            statuses[i],
        )

    # --- Fuel/energy price cache ---
    fuel_cache = {
        "petrol_95": 6.65,
        "diesel": 6.86,
        "electricity_kwh": 0.94,
    }
    await redis_client.setex("cache:fuel_prices", 3600, json.dumps(fuel_cache))

    # --- User sessions ---
    for i in range(3):
        session_data = {
            "user_id": str(USER_IDS[i]),
            "role": ["customer", "customer", "customer"][i],
            "login_at": (NOW - timedelta(hours=i + 1)).isoformat(),
        }
        session_token = f"session:{uuid.uuid4()}"
        await redis_client.setex(session_token, 86400, json.dumps(session_data))

    # --- Rate limiting counters ---
    for i in range(3):
        key = f"ratelimit:user:{USER_IDS[i]}"
        await redis_client.setex(key, 60, str(10 - i * 3))

    # --- Email queue placeholder ---
    email_tasks = [
        {
            "to": "jan.kowalski@example.com",
            "subject": "Przypomnienie o nadchodzącym wypożyczeniu",
            "rental_id": str(RENTAL_IDS[6]),
            "type": "reminder",
        },
        {
            "to": "piotr.wisniewski@example.com",
            "subject": "Potwierdzenie rezerwacji",
            "rental_id": str(RENTAL_IDS[4]),
            "type": "confirmation",
        },
    ]
    for task in email_tasks:
        await redis_client.rpush("queue:emails", json.dumps(task))

    total = await redis_client.dbsize()
    print(f"[REDIS] Seeded: {total} keys (availability, sessions, cache, queue)")

    await redis_client.aclose()


# ===========================================================================
# Main
# ===========================================================================
async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed DriveEase databases")
    parser.add_argument("--pg", action="store_true", help="Seed PostgreSQL only")
    parser.add_argument("--mongo", action="store_true", help="Seed MongoDB only")
    parser.add_argument("--redis", action="store_true", help="Seed Redis only")
    parser.add_argument("--drop", action="store_true", help="Drop existing data before seeding")
    args = parser.parse_args()

    seed_all = not (args.pg or args.mongo or args.redis)

    print("=== DriveEase Database Seeder ===\n")

    if seed_all or args.pg:
        await seed_postgres(drop=args.drop)
    if seed_all or args.mongo:
        await seed_mongo(drop=args.drop)
    if seed_all or args.redis:
        await seed_redis(drop=args.drop)

    print("\n=== Seeding complete ===")


if __name__ == "__main__":
    asyncio.run(main())
