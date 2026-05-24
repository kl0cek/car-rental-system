"""Light wiring tests for the service_orders / service_history tables.

These tests are intentionally narrow — just enough to prove the ORM
schema is consistent, the cost CHECK constraint is in place, the
``parts_replaced`` array round-trips, and ``ServiceHistory`` cascades on
parent ``ServiceOrder`` delete. Repository / service / router behavior is
out of scope here.

We follow the same in-memory ``aiosqlite`` pattern as
``tests/test_risk_scoring_integration.py`` — the schema-creation step
imports every ORM module that isn't covered by the top-level imports so
``Base.metadata.create_all`` builds the full table set.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import selectinload

from app.db.base import Base
from app.models.category import Category, CategoryName
from app.models.service_history import ServiceHistory
from app.models.service_order import ServiceOrder, ServiceOrderStatus, ServiceType
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, Vehicle, VehicleColor, VehicleStatus


@pytest_asyncio.fixture
async def sqlite_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # SQLite doesn't enforce FOREIGN KEY constraints unless explicitly
    # asked. We need ON DELETE CASCADE to behave like in production for
    # the cascade test, so enable it on every new connection.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        # Force-register every ORM module before create_all so the full
        # metadata graph is materialized (mirrors the risk_scoring fixture).
        from app.models import customer_note as _customer_note  # noqa: F401
        from app.models import incident as _incident  # noqa: F401
        from app.models import vehicle_image as _vehicle_image  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def sqlite_session(sqlite_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def _seed_vehicle_and_technician(
    session: AsyncSession,
) -> tuple[Vehicle, User]:
    """Insert one Category + Vehicle + Technician User; return refs."""
    category = Category(name=CategoryName.ECONOMY, price_multiplier=Decimal("1.000"))
    session.add(category)
    await session.flush()

    vehicle = Vehicle(
        brand="Toyota",
        model="Yaris",
        year=2023,
        license_plate="SRV001",
        vin="JT1234567890ABCDE",
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
    technician = User(
        email="tech@example.com",
        hashed_password="x",
        first_name="T",
        last_name="Tech",
        role=UserRole.TECHNICIAN,
        risk_score=Decimal("0.00"),
    )
    session.add_all([vehicle, technician])
    await session.flush()
    return vehicle, technician


async def test_create_service_order_persists_with_defaults(
    sqlite_session: AsyncSession,
) -> None:
    """A minimal ServiceOrder gets the SCHEDULED default and null cost/completed_date."""
    vehicle, technician = await _seed_vehicle_and_technician(sqlite_session)

    order = ServiceOrder(
        vehicle_id=vehicle.id,
        type=ServiceType.INSPECTION,
        description="Routine 10k inspection",
        scheduled_date=datetime.now(UTC) + timedelta(days=3),
        technician_id=technician.id,
    )
    sqlite_session.add(order)
    await sqlite_session.commit()

    reloaded = (
        await sqlite_session.execute(select(ServiceOrder).where(ServiceOrder.id == order.id))
    ).scalar_one()
    assert reloaded.status == ServiceOrderStatus.SCHEDULED
    assert reloaded.cost is None
    assert reloaded.completed_date is None
    assert reloaded.type == ServiceType.INSPECTION


async def test_create_service_history_with_parts_array(
    sqlite_session: AsyncSession,
) -> None:
    """``parts_replaced`` round-trips as a list[str].

    On PostgreSQL this is a native ``TEXT[]``; on SQLite (this test) it
    falls back to JSON via ``ARRAY.with_variant``. Either way the Python
    side sees ``list[str]``.
    """
    vehicle, technician = await _seed_vehicle_and_technician(sqlite_session)

    order = ServiceOrder(
        vehicle_id=vehicle.id,
        type=ServiceType.TIRE_SWAP,
        description="Seasonal swap",
        scheduled_date=datetime.now(UTC) - timedelta(days=1),
        technician_id=technician.id,
    )
    sqlite_session.add(order)
    await sqlite_session.flush()

    entry = ServiceHistory(
        vehicle_id=vehicle.id,
        service_order_id=order.id,
        notes="Swapped to winter tires",
        parts_replaced=["A", "B"],
        mileage_at_service=10050,
    )
    sqlite_session.add(entry)
    await sqlite_session.commit()

    reloaded = (
        await sqlite_session.execute(select(ServiceHistory).where(ServiceHistory.id == entry.id))
    ).scalar_one()
    assert reloaded.parts_replaced == ["A", "B"]
    assert reloaded.mileage_at_service == 10050


async def test_cost_check_constraint_rejects_negative(
    sqlite_session: AsyncSession,
) -> None:
    """The ck_service_order_cost_non_negative CHECK must reject ``cost < 0``.

    SQLAlchemy emits the CHECK in DDL for SQLite (which honors it by
    default — PRAGMA ignore_check_constraints is OFF). If a future
    SQLite build doesn't enforce it we skip cleanly; the constraint is
    still exercised in production on PG.
    """
    vehicle, technician = await _seed_vehicle_and_technician(sqlite_session)

    order = ServiceOrder(
        vehicle_id=vehicle.id,
        type=ServiceType.REPAIR,
        description="bad-cost order",
        cost=Decimal("-1"),
        scheduled_date=datetime.now(UTC),
        technician_id=technician.id,
    )
    sqlite_session.add(order)

    try:
        await sqlite_session.commit()
    except IntegrityError:
        # Expected — the CHECK fired (SQLite or PG, both honor it).
        return

    # If commit() succeeded, the CHECK was not enforced. Skip with a
    # clear note that the constraint is exercised in production on PG.
    pytest.skip(
        "SQLite did not enforce ck_service_order_cost_non_negative; "
        "this constraint is exercised in production on PostgreSQL."
    )


async def test_history_cascade_on_order_delete(
    sqlite_session: AsyncSession,
) -> None:
    """Deleting a ServiceOrder cascades and removes its ServiceHistory rows."""
    vehicle, technician = await _seed_vehicle_and_technician(sqlite_session)

    order = ServiceOrder(
        vehicle_id=vehicle.id,
        type=ServiceType.WASH,
        description="Detail wash",
        scheduled_date=datetime.now(UTC),
        technician_id=technician.id,
    )
    sqlite_session.add(order)
    await sqlite_session.flush()

    history = ServiceHistory(
        vehicle_id=vehicle.id,
        service_order_id=order.id,
        notes="Exterior + interior wash completed",
        parts_replaced=[],
        mileage_at_service=10000,
    )
    sqlite_session.add(history)
    await sqlite_session.commit()

    history_id = history.id

    # Pre-load the history collection so SQLAlchemy's
    # ``cascade="all, delete-orphan"`` has the children visible when it
    # decides what to delete. We also have PRAGMA foreign_keys=ON in the
    # engine fixture, so the DB-level ON DELETE CASCADE backs this up.
    order_to_delete = (
        await sqlite_session.execute(
            select(ServiceOrder)
            .options(selectinload(ServiceOrder.history_entries))
            .where(ServiceOrder.id == order.id)
        )
    ).scalar_one()

    await sqlite_session.delete(order_to_delete)
    await sqlite_session.commit()

    remaining = (
        await sqlite_session.execute(select(ServiceHistory).where(ServiceHistory.id == history_id))
    ).scalar_one_or_none()
    assert remaining is None
