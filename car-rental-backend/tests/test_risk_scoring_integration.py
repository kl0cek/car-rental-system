"""Integration test for the event-driven risk_score update path.

This test exercises ``recompute_and_persist`` end-to-end against a real
``AsyncSession`` (SQLite via ``aiosqlite``) to lock in the B1 fix:
mutating the loaded ``User`` ORM instance keeps the in-session object
consistent with the persisted value.

Why aiosqlite and not the running Postgres:
* The rest of the test suite is mock-based — there is no pre-existing
  live-DB fixture or precedent in ``conftest.py``. Spinning up an
  ad-hoc Postgres-backed fixture for one test is heavier than is
  warranted here.
* The behavior under test (ORM identity map staleness) is engine-agnostic
  — it is purely about how SQLAlchemy tracks the loaded instance.
* SQLite ignores ``postgresql_where`` partial indexes on the schema
  (used by ``vehicles`` and ``vehicle_images``); the test only touches
  ``users``, ``incidents``, ``reservations``, ``rentals``, ``vehicles``
  and ``categories``, none of which depend on those partial indexes
  for behavior.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.category import Category, CategoryName
from app.models.incident import Incident, IncidentSeverity, IncidentType
from app.models.rental import Rental, Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, Vehicle, VehicleColor, VehicleStatus
from app.services import risk_scoring


@pytest_asyncio.fixture
async def sqlite_engine() -> AsyncIterator[AsyncEngine]:
    """In-memory aiosqlite engine with the full ORM schema created.

    Exposed separately from the session so individual tests can spin up
    additional sessions against the same engine (e.g. to read from a
    fresh session bypassing the identity map).
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Import every ORM module so SQLAlchemy registers all tables on
        # Base.metadata before create_all. (The ones not imported at module
        # top would otherwise be missing.)
        from app.models import customer_note as _customer_note  # noqa: F401
        from app.models import vehicle_image as _vehicle_image  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def sqlite_session(sqlite_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Async SQLite session bound to ``sqlite_engine``."""
    session_factory = async_sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def test_recompute_updates_loaded_instance_and_persists(
    sqlite_engine: AsyncEngine,
    sqlite_session: AsyncSession,
) -> None:
    """End-to-end check of the B1 fix on a real DB.

    1. Create a User with risk_score=50 and one completed Rental.
    2. Insert an Incident (MAJOR, now) tied to that rental.
    3. Call ``recompute_and_persist``.
    4. Assert the returned score > 50, the loaded ORM instance reflects it
       (this is the staleness fix), and re-reading from a fresh session
       sees the same value.
    """
    now = datetime.now(UTC)

    # --- Seed users (customer + employee for the rental) ---
    customer = User(
        email="cust@example.com",
        hashed_password="x",
        first_name="C",
        last_name="X",
        role=UserRole.CUSTOMER,
        risk_score=Decimal("50.00"),
    )
    employee = User(
        email="emp@example.com",
        hashed_password="x",
        first_name="E",
        last_name="Y",
        role=UserRole.EMPLOYEE,
        risk_score=Decimal("0.00"),
    )
    sqlite_session.add_all([customer, employee])
    await sqlite_session.flush()

    # --- Seed a vehicle so we can attach a reservation/rental ---
    category = Category(name=CategoryName.ECONOMY, price_multiplier=Decimal("1.000"))
    sqlite_session.add(category)
    await sqlite_session.flush()

    vehicle = Vehicle(
        brand="Toyota",
        model="Yaris",
        year=2023,
        license_plate="ABC123",
        vin="JT123456789012345",
        engine_type=EngineType.PETROL,
        horsepower=100,
        seats=5,
        trunk_capacity=300,
        daily_base_price=Decimal("100.00"),
        color=VehicleColor.WHITE,
        mileage=10000,
        status=VehicleStatus.AVAILABLE,
        is_active=True,
        category_id=category.id,
    )
    sqlite_session.add(vehicle)
    await sqlite_session.flush()

    # --- One completed reservation + rental ---
    reservation = Reservation(
        user_id=customer.id,
        vehicle_id=vehicle.id,
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=5),
        status=ReservationStatus.COMPLETED,
        total_price=Decimal("500.00"),
    )
    sqlite_session.add(reservation)
    await sqlite_session.flush()

    rental = Rental(
        reservation_id=reservation.id,
        pickup_date=now - timedelta(days=10),
        return_date=now - timedelta(days=5),  # non-null → counts as completed
        mileage_start=10000,
        mileage_end=10500,
        fuel_level_start=Decimal("100.00"),
        fuel_level_end=Decimal("80.00"),
        employee_id=employee.id,
    )
    sqlite_session.add(rental)
    await sqlite_session.flush()

    # --- Major incident tied to the completed rental ---
    # NB: We set created_at explicitly because SQLite's ``func.now()`` produces
    # a naive timestamp; the recency-decay math subtracts it from a tz-aware
    # ``datetime.now(UTC)`` and would otherwise raise.
    incident = Incident(
        customer_id=customer.id,
        rental_id=rental.id,
        reported_by_id=employee.id,
        type=IncidentType.DAMAGE,
        severity=IncidentSeverity.MAJOR,
        title="Major damage",
        description="Door bent",
        created_at=now,
    )
    sqlite_session.add(incident)
    await sqlite_session.commit()

    # --- Act: recompute on the same session that already holds `customer` ---
    customer_id = customer.id
    new_score = await risk_scoring.recompute_and_persist(sqlite_session, customer_id)
    await sqlite_session.commit()

    # (a) Returned score is higher than the seeded 50 (major incident now).
    assert new_score > Decimal("50.00")

    # (c) The already-loaded ORM instance reflects the new value — the
    #     whole point of the B1 fix vs. the old Core UPDATE.
    assert customer.risk_score == new_score

    # (b) A fresh session sees the persisted value. Build a second session
    #     against the same engine to bypass identity map effects.
    second_session_factory = async_sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    async with second_session_factory() as fresh:
        from sqlalchemy import select as sa_select

        reloaded = (await fresh.execute(sa_select(User).where(User.id == customer_id))).scalar_one()
        assert reloaded.risk_score == new_score


async def test_recompute_raises_404_for_unknown_user(
    sqlite_session: AsyncSession,
) -> None:
    """B1/B3 on a real DB: bogus user_id raises 404, not silent no-op."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await risk_scoring.recompute_and_persist(sqlite_session, uuid.uuid4())
    assert exc_info.value.status_code == 404
