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
RESERVATION_IDS = [uuid.uuid4() for _ in range(10)]
# Active rental IDs — only for reservations that reached pickup (indices 0,1,2,3,5,7,9)
ACTIVE_RENTAL_IDS = [uuid.uuid4() for _ in range(7)]

NOW = datetime.now(UTC)


# ===========================================================================
# Bulk-insert helpers (czysty SQL przez asyncpg, kolumny created_at/updated_at
# wypełnia baza DEFAULT now()). Obiekty są dataclassami — czytamy ich pola,
# a wartości enumów zapisujemy jako .value.
# ===========================================================================
async def _insert_users(conn: object, users: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO users (id, email, hashed_password, first_name, last_name, role, "
        "is_active, is_verified, phone, avatar_url, risk_score, last_login_at) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
        [
            (
                u.id,
                u.email,
                u.hashed_password,
                u.first_name,
                u.last_name,
                u.role.value,
                u.is_active,
                u.is_verified,
                u.phone,
                u.avatar_url,
                u.risk_score,
                u.last_login_at,
            )
            for u in users
        ],
    )


async def _insert_categories(conn: object, categories: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO categories (id, name, description, price_multiplier) VALUES ($1, $2, $3, $4)",
        [(c.id, c.name.value, c.description, c.price_multiplier) for c in categories],
    )


async def _insert_vehicles(conn: object, vehicles: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO vehicles (id, brand, model, year, license_plate, vin, engine_type, "
        "horsepower, seats, trunk_capacity, daily_base_price, color, mileage, status, "
        "is_active, avg_rating, ratings_count, category_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)",
        [
            (
                v.id,
                v.brand,
                v.model,
                v.year,
                v.license_plate,
                v.vin,
                v.engine_type.value,
                v.horsepower,
                v.seats,
                v.trunk_capacity,
                v.daily_base_price,
                v.color.value,
                v.mileage,
                v.status.value,
                v.is_active,
                v.avg_rating,
                v.ratings_count,
                v.category_id,
            )
            for v in vehicles
        ],
    )


async def _insert_vehicle_images(conn: object, images: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO vehicle_images (id, vehicle_id, url, position, is_primary) "
        "VALUES ($1, $2, $3, $4, $5)",
        [(i.id, i.vehicle_id, i.url, i.position, i.is_primary) for i in images],
    )


async def _insert_reservations(conn: object, reservations: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO reservations (id, user_id, vehicle_id, start_date, end_date, status, "
        "total_price) VALUES ($1, $2, $3, $4, $5, $6, $7)",
        [
            (r.id, r.user_id, r.vehicle_id, r.start_date, r.end_date, r.status.value, r.total_price)
            for r in reservations
        ],
    )


async def _insert_rentals(conn: object, rentals: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO rentals (id, reservation_id, pickup_date, return_date, mileage_start, "
        "mileage_end, fuel_level_start, fuel_level_end, damage_notes, employee_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
        [
            (
                r.id,
                r.reservation_id,
                r.pickup_date,
                r.return_date,
                r.mileage_start,
                r.mileage_end,
                r.fuel_level_start,
                r.fuel_level_end,
                r.damage_notes,
                r.employee_id,
            )
            for r in rentals
        ],
    )


async def _insert_price_breakdowns(conn: object, breakdowns: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO rental_price_breakdowns (id, rental_id, base_price, risk_multiplier, "
        "final_price) VALUES ($1, $2, $3, $4, $5)",
        [(b.id, b.rental_id, b.base_price, b.risk_multiplier, b.final_price) for b in breakdowns],
    )


async def _insert_incidents(conn: object, incidents: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO incidents (id, customer_id, rental_id, reported_by_id, type, severity, "
        "title, description, cost) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
        [
            (
                i.id,
                i.customer_id,
                i.rental_id,
                i.reported_by_id,
                i.type.value,
                i.severity.value,
                i.title,
                i.description,
                i.cost,
            )
            for i in incidents
        ],
    )


async def _insert_service_orders(conn: object, orders: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO service_orders (id, vehicle_id, type, status, description, cost, "
        "scheduled_date, completed_date, technician_id) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
        [
            (
                o.id,
                o.vehicle_id,
                o.type.value,
                o.status.value,
                o.description,
                o.cost,
                o.scheduled_date,
                o.completed_date,
                o.technician_id,
            )
            for o in orders
        ],
    )


async def _insert_service_history(conn: object, entries: list) -> None:
    await conn.executemany(  # type: ignore[attr-defined]
        "INSERT INTO service_history (id, vehicle_id, service_order_id, notes, parts_replaced, "
        "mileage_at_service) VALUES ($1, $2, $3, $4, $5, $6)",
        [
            (
                e.id,
                e.vehicle_id,
                e.service_order_id,
                e.notes,
                e.parts_replaced,
                e.mileage_at_service,
            )
            for e in entries
        ],
    )


# ===========================================================================
# PostgreSQL seed
# ===========================================================================
async def seed_postgres(*, drop: bool = False) -> None:
    import asyncpg

    from app.config import settings
    from app.core.security import hash_password
    from app.db.bootstrap import SCHEMA_PATH
    from app.models.category import Category, CategoryName
    from app.models.incident import Incident, IncidentSeverity, IncidentType
    from app.models.rental import Rental, RentalPriceBreakdown, Reservation, ReservationStatus
    from app.models.service_history import ServiceHistory
    from app.models.service_order import ServiceOrder, ServiceOrderStatus, ServiceType
    from app.models.user import User, UserRole
    from app.models.vehicle import EngineType, Vehicle, VehicleColor, VehicleStatus
    from app.models.vehicle_image import VehicleImage

    conn = await asyncpg.connect(settings.postgres_dsn)
    if drop:
        await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        print("[PG] Dropped all tables")
    # Schemat z jawnego pliku DDL (ten sam, którego używa bootstrap aplikacji).
    await conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
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
            # Low-risk customer — score < 20 → 0.80 multiplier (discount).
            risk_score=Decimal("0.00"),
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
            # Moderate-risk customer — score in [20, 40) → 0.90 multiplier.
            risk_score=Decimal("35.00"),
        ),
        User(
            id=USER_IDS[2],
            email="piotr.wisniewski@example.com",
            hashed_password=seed_password,
            first_name="Piotr",
            last_name="Wiśniewski",
            role=UserRole.CUSTOMER,
            is_verified=True,
            # Higher-risk customer — score in [60, 80) → 1.20 multiplier.
            risk_score=Decimal("60.00"),
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
            color=VehicleColor.WHITE,
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
            color=VehicleColor.GREY,
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
            color=VehicleColor.BLACK,
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
            color=VehicleColor.GREEN,
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
            color=VehicleColor.BLUE,
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
            color=VehicleColor.BLACK,
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
            color=VehicleColor.WHITE,
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
            color=VehicleColor.RED,
            mileage=95000,
            status=VehicleStatus.OUT_OF_SERVICE,
            category_id=CATEGORY_IDS[0],
        ),
    ]

    # --- Reservations (formerly Rentals) ---
    reservations = [
        Reservation(
            id=RESERVATION_IDS[0],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=30),
            end_date=NOW - timedelta(days=25),
            total_price=Decimal("750.00"),
            status=ReservationStatus.COMPLETED,
        ),
        Reservation(
            id=RESERVATION_IDS[1],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[2],
            start_date=NOW - timedelta(days=15),
            end_date=NOW - timedelta(days=12),
            total_price=Decimal("1050.00"),
            status=ReservationStatus.COMPLETED,
        ),
        Reservation(
            id=RESERVATION_IDS[2],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[1],
            start_date=NOW - timedelta(days=3),
            end_date=NOW + timedelta(days=4),
            total_price=Decimal("1190.00"),
            status=ReservationStatus.ACTIVE,
        ),
        Reservation(
            id=RESERVATION_IDS[3],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[3],
            start_date=NOW - timedelta(days=60),
            end_date=NOW - timedelta(days=55),
            total_price=Decimal("1400.00"),
            status=ReservationStatus.COMPLETED,
        ),
        Reservation(
            id=RESERVATION_IDS[4],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[5],
            start_date=NOW + timedelta(days=2),
            end_date=NOW + timedelta(days=5),
            total_price=Decimal("960.00"),
            status=ReservationStatus.PENDING,
        ),
        Reservation(
            id=RESERVATION_IDS[5],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=90),
            end_date=NOW - timedelta(days=85),
            total_price=Decimal("750.00"),
            status=ReservationStatus.COMPLETED,
        ),
        Reservation(
            id=RESERVATION_IDS[6],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[6],
            start_date=NOW + timedelta(days=7),
            end_date=NOW + timedelta(days=14),
            total_price=Decimal("1750.00"),
            status=ReservationStatus.CONFIRMED,
        ),
        Reservation(
            id=RESERVATION_IDS[7],
            user_id=USER_IDS[1],
            vehicle_id=VEHICLE_IDS[0],
            start_date=NOW - timedelta(days=120),
            end_date=NOW - timedelta(days=117),
            total_price=Decimal("450.00"),
            status=ReservationStatus.COMPLETED,
        ),
        Reservation(
            id=RESERVATION_IDS[8],
            user_id=USER_IDS[2],
            vehicle_id=VEHICLE_IDS[3],
            start_date=NOW - timedelta(days=45),
            end_date=NOW - timedelta(days=44),
            total_price=Decimal("280.00"),
            status=ReservationStatus.CANCELLED,
        ),
        Reservation(
            id=RESERVATION_IDS[9],
            user_id=USER_IDS[0],
            vehicle_id=VEHICLE_IDS[4],
            start_date=NOW - timedelta(days=200),
            end_date=NOW - timedelta(days=193),
            total_price=Decimal("980.00"),
            status=ReservationStatus.COMPLETED,
        ),
    ]

    # --- Active Rentals (only for reservations that reached pickup stage) ---
    # employee USER_IDS[3] (Marta Zielińska) handled all pickups
    active_rentals = [
        # arl[0]: res[0] — Toyota Corolla, completed
        Rental(
            id=ACTIVE_RENTAL_IDS[0],
            reservation_id=RESERVATION_IDS[0],
            pickup_date=NOW - timedelta(days=30),
            return_date=NOW - timedelta(days=25),
            mileage_start=24500,
            mileage_end=25000,
            fuel_level_start=Decimal("75.00"),
            fuel_level_end=Decimal("55.00"),
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[1]: res[1] — Tesla Model 3, completed
        Rental(
            id=ACTIVE_RENTAL_IDS[1],
            reservation_id=RESERVATION_IDS[1],
            pickup_date=NOW - timedelta(days=15),
            return_date=NOW - timedelta(days=12),
            mileage_start=7500,
            mileage_end=8000,
            fuel_level_start=Decimal("90.00"),
            fuel_level_end=Decimal("45.00"),
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[2]: res[2] — VW Golf, currently active (no return yet)
        Rental(
            id=ACTIVE_RENTAL_IDS[2],
            reservation_id=RESERVATION_IDS[2],
            pickup_date=NOW - timedelta(days=3),
            return_date=None,
            mileage_start=44800,
            mileage_end=None,
            fuel_level_start=Decimal("80.00"),
            fuel_level_end=None,
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[3]: res[3] — Toyota RAV4 Hybrid, completed
        Rental(
            id=ACTIVE_RENTAL_IDS[3],
            reservation_id=RESERVATION_IDS[3],
            pickup_date=NOW - timedelta(days=60),
            return_date=NOW - timedelta(days=55),
            mileage_start=17300,
            mileage_end=18000,
            fuel_level_start=Decimal("85.00"),
            fuel_level_end=Decimal("70.00"),
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[4]: res[5] — Toyota Corolla, completed
        Rental(
            id=ACTIVE_RENTAL_IDS[4],
            reservation_id=RESERVATION_IDS[5],
            pickup_date=NOW - timedelta(days=90),
            return_date=NOW - timedelta(days=85),
            mileage_start=19800,
            mileage_end=20500,
            fuel_level_start=Decimal("100.00"),
            fuel_level_end=Decimal("60.00"),
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[5]: res[7] — Toyota Corolla, completed
        Rental(
            id=ACTIVE_RENTAL_IDS[5],
            reservation_id=RESERVATION_IDS[7],
            pickup_date=NOW - timedelta(days=120),
            return_date=NOW - timedelta(days=117),
            mileage_start=22500,
            mileage_end=23000,
            fuel_level_start=Decimal("90.00"),
            fuel_level_end=Decimal("75.00"),
            damage_notes=None,
            employee_id=USER_IDS[3],
        ),
        # arl[6]: res[9] — Skoda Octavia, completed (minor damage noted)
        Rental(
            id=ACTIVE_RENTAL_IDS[6],
            reservation_id=RESERVATION_IDS[9],
            pickup_date=NOW - timedelta(days=200),
            return_date=NOW - timedelta(days=193),
            mileage_start=64000,
            mileage_end=65200,
            fuel_level_start=Decimal("80.00"),
            fuel_level_end=Decimal("50.00"),
            damage_notes="Drobne zarysowanie zderzaka przedniego na parkingu.",
            employee_id=USER_IDS[3],
        ),
    ]

    # --- Rental Price Breakdowns (for all completed/active rentals) ---
    # Use the production helper so seeded final_price values respect the
    # invariant enforced by rental_service.return_rental:
    #   final_price == base_price * risk_multiplier
    # Importing here (not at module top) keeps the script's imports lazy.
    from app.services.rental_service import compute_risk_multiplier

    risk_by_user = {
        USER_IDS[0]: compute_risk_multiplier(Decimal("0.00")),
        USER_IDS[1]: compute_risk_multiplier(Decimal("35.00")),
        USER_IDS[2]: compute_risk_multiplier(Decimal("60.00")),
    }
    reservation_by_id = {r.id: r for r in reservations}

    def _make_breakdown(rental: Rental) -> RentalPriceBreakdown:
        reservation = reservation_by_id[rental.reservation_id]
        base_price = reservation.total_price.quantize(Decimal("0.01"))
        risk_multiplier = risk_by_user[reservation.user_id]
        final_price = (base_price * risk_multiplier).quantize(Decimal("0.01"))
        return RentalPriceBreakdown(
            rental_id=rental.id,
            base_price=base_price,
            risk_multiplier=risk_multiplier,
            final_price=final_price,
        )

    price_breakdowns = [_make_breakdown(r) for r in active_rentals]

    # --- Incidents (PG) — exercise the new cost column and renamed severity enum.
    # Tied to ACTIVE_RENTAL_IDS[6] (Skoda Octavia minor scratch noted in seed).
    incidents_pg = [
        Incident(
            customer_id=USER_IDS[0],
            rental_id=ACTIVE_RENTAL_IDS[6],
            reported_by_id=USER_IDS[3],  # Marta Zielińska (employee)
            type=IncidentType.DAMAGE,
            severity=IncidentSeverity.MINOR,
            title="Zarysowanie zderzaka",
            description="Drobne zarysowanie zderzaka przedniego na parkingu.",
            cost=Decimal("450.00"),
        ),
    ]

    # --- Service orders & history --------------------------------------------
    # Demonstrate the full ScheduledInspection → InProgressRepair →
    # CompletedTireSwap lifecycle. Technician = USER_IDS[4] (Tomasz
    # Lewandowski). Vehicle mileages: Corolla=25000, Golf=45000, Tesla=8000.
    completed_tire_swap_id = uuid.uuid4()
    service_orders = [
        ServiceOrder(
            vehicle_id=VEHICLE_IDS[0],
            type=ServiceType.INSPECTION,
            status=ServiceOrderStatus.SCHEDULED,
            description="Przegląd okresowy 25 000 km — wymiana oleju, filtrów.",
            cost=None,
            scheduled_date=NOW + timedelta(days=7),
            completed_date=None,
            technician_id=USER_IDS[4],
        ),
        ServiceOrder(
            vehicle_id=VEHICLE_IDS[1],
            type=ServiceType.REPAIR,
            status=ServiceOrderStatus.IN_PROGRESS,
            description="Wymiana klocków hamulcowych — przód oraz tarcz.",
            cost=Decimal("680.00"),
            scheduled_date=NOW - timedelta(days=2),
            completed_date=None,
            technician_id=USER_IDS[4],
        ),
        ServiceOrder(
            id=completed_tire_swap_id,
            vehicle_id=VEHICLE_IDS[2],
            type=ServiceType.TIRE_SWAP,
            status=ServiceOrderStatus.COMPLETED,
            description="Sezonowa wymiana opon na zimowe.",
            cost=Decimal("220.00"),
            scheduled_date=NOW - timedelta(days=10),
            completed_date=NOW - timedelta(days=9),
            technician_id=USER_IDS[4],
        ),
    ]

    # One history record for the completed tire swap — Tesla currently at
    # mileage 8000, service captured at ~+100 km.
    service_history = [
        ServiceHistory(
            vehicle_id=VEHICLE_IDS[2],
            service_order_id=completed_tire_swap_id,
            notes="Wymieniono komplet opon zimowych. Pojazd gotowy do odbioru.",
            parts_replaced=["Opona zimowa 205/55R16 x4"],
            mileage_at_service=8100,
        ),
    ]

    # --- Vehicle images (one primary per vehicle, mapping VEHICLE_IDS -> URL) ---
    vehicle_image_urls = [
        "https://images.unsplash.com/photo-1623869675781-80aa31012a5a?w=800&q=80",
        "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?w=800&q=80",
        "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=800&q=80",
        "https://images.unsplash.com/photo-1568844293986-8d0400b5d25f?w=800&q=80",
        "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=800&q=80",
        "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800&q=80",
        "https://images.unsplash.com/photo-1593941707874-ef25b8b4a92b?w=800&q=80",
        "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800&q=80",
    ]
    vehicle_images = [
        VehicleImage(
            vehicle_id=VEHICLE_IDS[i],
            url=url,
            position=0,
            is_primary=True,
        )
        for i, url in enumerate(vehicle_image_urls)
    ]

    # Check if data already exists
    count = await conn.fetchval("SELECT count(*) FROM users")
    if count and count > 0:
        print(f"[PG] Skipping — {count} users already exist (use --drop to reset)")
        await conn.close()
        return

    # Jedna transakcja, kolejność zgodna z zależnościami kluczy obcych.
    async with conn.transaction():
        await _insert_users(conn, users)
        await _insert_categories(conn, categories)
        await _insert_vehicles(conn, vehicles)
        await _insert_vehicle_images(conn, vehicle_images)
        await _insert_reservations(conn, reservations)
        await _insert_rentals(conn, active_rentals)
        await _insert_price_breakdowns(conn, price_breakdowns)
        await _insert_incidents(conn, incidents_pg)
        await _insert_service_orders(conn, service_orders)
        await _insert_service_history(conn, service_history)

    print(
        f"[PG] Seeded: {len(users)} users, {len(categories)} categories, "
        f"{len(vehicles)} vehicles, {len(vehicle_images)} vehicle images, "
        f"{len(reservations)} reservations, "
        f"{len(active_rentals)} active rentals, {len(price_breakdowns)} price breakdowns, "
        f"{len(incidents_pg)} incidents, "
        f"{len(service_orders)} service orders, {len(service_history)} service history entries"
    )

    await conn.close()


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

    # rental_id here refers to the active Rental (ACTIVE_RENTAL_IDS), not reservation
    rental_logs = [
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[0]),
            "reservation_id": str(RESERVATION_IDS[0]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=30)).isoformat(),
            "mileage_at_event": 24500,
            "location": "Warszawa - oddział główny",
        },
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[0]),
            "reservation_id": str(RESERVATION_IDS[0]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "action": "return",
            "timestamp": (NOW - timedelta(days=25)).isoformat(),
            "mileage_at_event": 25000,
            "location": "Warszawa - oddział główny",
            "fuel_level": 55.0,
        },
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[2]),
            "reservation_id": str(RESERVATION_IDS[2]),
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[1]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=3)).isoformat(),
            "mileage_at_event": 44800,
            "location": "Kraków - lotnisko",
        },
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[1]),
            "reservation_id": str(RESERVATION_IDS[1]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "action": "pickup",
            "timestamp": (NOW - timedelta(days=15)).isoformat(),
            "mileage_at_event": 7500,
            "location": "Gdańsk - centrum",
        },
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[1]),
            "reservation_id": str(RESERVATION_IDS[1]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "action": "return",
            "timestamp": (NOW - timedelta(days=12)).isoformat(),
            "mileage_at_event": 8000,
            "location": "Gdańsk - centrum",
            "battery_level": 45.0,
        },
    ]

    # --- Reviews ---
    # rental_id refers to the actual Rental record (post-pickup), not the Reservation.
    # Uniqueness is enforced by a compound (rental_id, user_id) index in MongoDB.
    # ``author`` snapshots the user's display info at write time so the public
    # listing endpoint stays one round-trip (matches review_repository.insert).
    _seed_authors = {
        str(USER_IDS[0]): {"first_name": "Jan", "last_name": "Kowalski"},
        str(USER_IDS[1]): {"first_name": "Anna", "last_name": "Nowak"},
        str(USER_IDS[2]): {"first_name": "Piotr", "last_name": "Wiśniewski"},
    }

    def _review_author(user_id: uuid.UUID) -> dict[str, object]:
        info = _seed_authors[str(user_id)]
        return {
            "id": str(user_id),
            "first_name": info["first_name"],
            "last_name": info["last_name"],
            "avatar_url": None,
        }

    reviews = [
        {
            "_id": str(uuid.uuid4()),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "rental_id": str(ACTIVE_RENTAL_IDS[0]),
            "rating": 5,
            "comment": "Świetny samochód, czysty i zadbany. Polecam!",
            "created_at": NOW - timedelta(days=24),
            "author": _review_author(USER_IDS[0]),
        },
        {
            "_id": str(uuid.uuid4()),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[2]),
            "rental_id": str(ACTIVE_RENTAL_IDS[1]),
            "rating": 4,
            "comment": "Tesla super, ale zasięg mniejszy niż obiecany.",
            "created_at": NOW - timedelta(days=11),
            "author": _review_author(USER_IDS[0]),
        },
        {
            "_id": str(uuid.uuid4()),
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[3]),
            "rental_id": str(ACTIVE_RENTAL_IDS[3]),
            "rating": 5,
            "comment": "RAV4 Hybrid idealny na dłuższą trasę. Niskie spalanie.",
            "created_at": NOW - timedelta(days=54),
            "author": _review_author(USER_IDS[1]),
        },
        {
            "_id": str(uuid.uuid4()),
            "user_id": str(USER_IDS[2]),
            "vehicle_id": str(VEHICLE_IDS[0]),
            "rental_id": str(ACTIVE_RENTAL_IDS[4]),
            "rating": 3,
            "comment": "Samochód OK, ale trochę hałaśliwy silnik.",
            "created_at": NOW - timedelta(days=84),
            "author": _review_author(USER_IDS[2]),
        },
    ]

    # --- Incidents ---
    incidents = [
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[6]),
            "reservation_id": str(RESERVATION_IDS[9]),
            "user_id": str(USER_IDS[0]),
            "vehicle_id": str(VEHICLE_IDS[4]),
            "type": "minor_damage",
            "description": "Drobne zarysowanie zderzaka przedniego na parkingu.",
            "severity": "minor",
            "reported_at": (NOW - timedelta(days=195)).isoformat(),
            "resolved": True,
            "repair_cost": 450.00,
        },
        {
            "rental_id": str(ACTIVE_RENTAL_IDS[3]),
            "reservation_id": str(RESERVATION_IDS[3]),
            "user_id": str(USER_IDS[1]),
            "vehicle_id": str(VEHICLE_IDS[3]),
            "type": "flat_tire",
            "description": "Przebita opona na autostradzie A4. Wymieniono na zapasową.",
            "severity": "moderate",
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

    from app.repositories import review_repository

    # Ensure the reviews collection has its validator + unique (rental_id, user_id)
    # index in place BEFORE inserting, so the seed runs against the same schema
    # the production app enforces.
    await review_repository.ensure_collection(mongo_db)

    await mongo_db.rental_logs.insert_many(rental_logs)
    await mongo_db.reviews.insert_many(reviews)
    await mongo_db.incidents.insert_many(incidents)
    await mongo_db.user_preferences.insert_many(user_preferences)

    # Create indexes
    await mongo_db.rental_logs.create_index("rental_id")
    await mongo_db.rental_logs.create_index("reservation_id")
    await mongo_db.rental_logs.create_index("user_id")
    # reviews indexes are owned by review_repository.ensure_collection above.
    await mongo_db.incidents.create_index("rental_id")
    await mongo_db.incidents.create_index("reservation_id")
    await mongo_db.user_preferences.create_index("user_id", unique=True)

    # Propagate review aggregates onto vehicles (avg_rating / ratings_count) so
    # the Postgres-side denormalised columns match the seeded Mongo state.
    await _backfill_vehicle_review_aggregates(mongo_db)

    print(
        f"[MONGO] Seeded: {len(rental_logs)} logs, {len(reviews)} reviews, "
        f"{len(incidents)} incidents, "
        f"{len(user_preferences)} user preferences"
    )


async def _backfill_vehicle_review_aggregates(mongo_db: object) -> None:
    """Recompute avg_rating / ratings_count on vehicles from the seeded Mongo reviews.

    Mirrors the runtime behaviour of ``review_service._refresh_vehicle_rating``
    but in a single bulk pass so the seed leaves both databases consistent.
    """
    import asyncpg

    from app.config import settings

    pipeline = [
        {
            "$group": {
                "_id": "$vehicle_id",
                "avg": {"$avg": "$rating"},
                "count": {"$sum": 1},
            }
        }
    ]
    aggregates = await mongo_db.reviews.aggregate(pipeline).to_list(length=None)  # type: ignore[attr-defined]

    conn = await asyncpg.connect(settings.postgres_dsn)
    try:
        async with conn.transaction():
            for row in aggregates:
                await conn.execute(
                    "UPDATE vehicles SET avg_rating = $2, ratings_count = $3, "
                    "updated_at = now() WHERE id = $1",
                    uuid.UUID(row["_id"]),
                    Decimal(str(round(row["avg"], 2))),
                    int(row["count"]),
                )
    finally:
        await conn.close()


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
            "subject": "Potwierdzenie rezerwacji",
            "reservation_id": str(RESERVATION_IDS[6]),
            "type": "confirmation",
        },
        {
            "to": "piotr.wisniewski@example.com",
            "subject": "Przypomnienie o nadchodzącym wypożyczeniu",
            "reservation_id": str(RESERVATION_IDS[4]),
            "type": "reminder",
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
