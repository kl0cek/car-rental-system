import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import Category, CategoryName
from app.models.rental import Rental, RentalStatus
from app.models.user import User
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

POSTGRES_IMAGE = "postgres:17-alpine"


# ---------------------------------------------------------------------------
# Container (session scope, sync)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer(POSTGRES_IMAGE, driver="asyncpg") as pg:
        yield pg.get_connection_url()


# ---------------------------------------------------------------------------
# Engine + tables (created fresh per-module to avoid event loop issues)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def _engine_and_tables(postgres_url):
    """Create engine on the current event loop, set up tables, tear down after."""
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Per-test transactional session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db(_engine_and_tables):
    """Transactional session — rolls back after each test."""
    engine = _engine_and_tables
    conn = await engine.connect()
    txn = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)

    yield session

    await session.close()
    await txn.rollback()
    await conn.close()


# ---------------------------------------------------------------------------
# HTTP client wired to the real test database
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db):
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def category_economy(db: AsyncSession) -> Category:
    cat = Category(
        name=CategoryName.ECONOMY, description="Budget", price_multiplier=Decimal("1.000")
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def category_comfort(db: AsyncSession) -> Category:
    cat = Category(
        name=CategoryName.COMFORT,
        description="Comfort class",
        price_multiplier=Decimal("1.200"),
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def category_premium(db: AsyncSession) -> Category:
    cat = Category(
        name=CategoryName.PREMIUM,
        description="Premium class",
        price_multiplier=Decimal("1.500"),
    )
    db.add(cat)
    await db.flush()
    return cat


@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    u = User(
        email="test@driveease.com",
        hashed_password="fakehash",
        first_name="Jan",
        last_name="Kowalski",
        is_verified=True,
    )
    db.add(u)
    await db.flush()
    return u


def _make_vehicle(category: Category, **overrides) -> Vehicle:
    """Helper to build a Vehicle with sensible defaults."""
    defaults = dict(
        brand="Toyota",
        model="Corolla",
        year=2023,
        license_plate=f"WA {uuid.uuid4().hex[:5].upper()}",
        vin=uuid.uuid4().hex[:17].upper(),
        engine_type=EngineType.PETROL,
        horsepower=140,
        seats=5,
        trunk_capacity=361,
        daily_base_price=Decimal("150.00"),
        color="White",
        mileage=25000,
        status=VehicleStatus.AVAILABLE,
        is_active=True,
        category_id=category.id,
    )
    defaults.update(overrides)
    return Vehicle(**defaults)


@pytest_asyncio.fixture
async def vehicle(db: AsyncSession, category_economy: Category) -> Vehicle:
    v = _make_vehicle(category_economy)
    db.add(v)
    await db.flush()
    return v


@pytest_asyncio.fixture
async def vehicle_comfort(db: AsyncSession, category_comfort: Category) -> Vehicle:
    v = _make_vehicle(
        category_comfort,
        brand="BMW",
        model="3 Series",
        year=2024,
        engine_type=EngineType.DIESEL,
        horsepower=190,
        seats=5,
        daily_base_price=Decimal("300.00"),
        color="Black",
        mileage=5000,
    )
    db.add(v)
    await db.flush()
    return v


@pytest_asyncio.fixture
async def vehicle_inactive(db: AsyncSession, category_economy: Category) -> Vehicle:
    v = _make_vehicle(category_economy, is_active=False)
    db.add(v)
    await db.flush()
    return v


@pytest_asyncio.fixture
async def rental_active(db: AsyncSession, user: User, vehicle: Vehicle) -> Rental:
    now = datetime.now(UTC)
    r = Rental(
        user_id=user.id,
        vehicle_id=vehicle.id,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=5),
        total_price=Decimal("750.00"),
        status=RentalStatus.ACTIVE,
    )
    db.add(r)
    await db.flush()
    return r


@pytest_asyncio.fixture
async def rental_pending_future(db: AsyncSession, user: User, vehicle: Vehicle) -> Rental:
    now = datetime.now(UTC)
    r = Rental(
        user_id=user.id,
        vehicle_id=vehicle.id,
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=15),
        total_price=Decimal("750.00"),
        status=RentalStatus.PENDING,
    )
    db.add(r)
    await db.flush()
    return r
