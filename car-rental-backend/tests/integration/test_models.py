"""Verify models, relations, and constraints against a real PostgreSQL database."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models.category import Category, CategoryName
from app.models.rental import Rental, RentalStatus
from app.models.user import User
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Schema creation on clean DB
# ---------------------------------------------------------------------------


class TestSchemaCreation:
    async def test_all_tables_created(self, db: AsyncSession):
        # Given: tables created via Base.metadata.create_all

        # When
        result = await db.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
        )
        tables = {row[0] for row in result.all()}

        # Then
        assert "categories" in tables
        assert "vehicles" in tables
        assert "users" in tables
        assert "rentals" in tables

    async def test_vehicle_table_has_expected_columns(self, db: AsyncSession):
        # Given: vehicles table created from the Vehicle model

        # When
        result = await db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'vehicles' ORDER BY ordinal_position"
            )
        )
        columns = {row[0] for row in result.all()}

        # Then
        expected = {
            "id", "brand", "model", "year", "license_plate", "vin",
            "engine_type", "horsepower", "seats", "trunk_capacity",
            "daily_base_price", "color", "mileage", "image_url",
            "status", "is_active", "category_id", "created_at", "updated_at",
        }
        assert expected.issubset(columns)

    async def test_categories_table_has_expected_columns(self, db: AsyncSession):
        # Given: categories table created from the Category model

        # When
        result = await db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'categories' ORDER BY ordinal_position"
            )
        )
        columns = {row[0] for row in result.all()}

        # Then
        assert {
            "id", "name", "description", "price_multiplier", "created_at", "updated_at"
        }.issubset(columns)


# ---------------------------------------------------------------------------
# Foreign key relations
# ---------------------------------------------------------------------------


class TestRelations:
    async def test_vehicle_belongs_to_category(self, vehicle, category_economy):
        # Given: a vehicle created with economy category

        # Then
        assert vehicle.category_id == category_economy.id

    async def test_category_has_vehicles(self, db: AsyncSession, vehicle, category_economy):
        # Given: a vehicle assigned to economy category

        # When
        await db.refresh(category_economy, ["vehicles"])

        # Then
        assert vehicle in category_economy.vehicles

    async def test_rental_belongs_to_user_and_vehicle(self, rental_active, user, vehicle):
        # Given: an active rental linking a user and a vehicle

        # Then
        assert rental_active.user_id == user.id
        assert rental_active.vehicle_id == vehicle.id

    async def test_user_has_rentals(self, db: AsyncSession, rental_active, user):
        # Given: a user with an active rental

        # When
        await db.refresh(user, ["rentals"])

        # Then
        assert rental_active in user.rentals

    async def test_vehicle_has_rentals(self, db: AsyncSession, rental_active, vehicle):
        # Given: a vehicle with an active rental

        # When
        await db.refresh(vehicle, ["rentals"])

        # Then
        assert rental_active in vehicle.rentals

    async def test_vehicle_fk_rejects_invalid_category(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        v = _make_vehicle(category_economy, category_id=uuid.uuid4())
        db.add(v)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()

    async def test_rental_fk_rejects_invalid_vehicle(self, db: AsyncSession, user):
        # Given
        r = Rental(
            user_id=user.id,
            vehicle_id=uuid.uuid4(),
            start_date=user.created_at,
            end_date=user.created_at,
            total_price=Decimal("100.00"),
            status=RentalStatus.PENDING,
        )
        db.add(r)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()


# ---------------------------------------------------------------------------
# Check constraints (PostgreSQL enforces these)
# ---------------------------------------------------------------------------


class TestConstraints:
    async def test_horsepower_must_be_positive(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        v = _make_vehicle(category_economy, horsepower=0)
        db.add(v)

        # When/Then
        with pytest.raises(IntegrityError, match="ck_vehicle_horsepower_positive"):
            await db.flush()

    async def test_seats_must_be_positive(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        v = _make_vehicle(category_economy, seats=0)
        db.add(v)

        # When/Then
        with pytest.raises(IntegrityError, match="ck_vehicle_seats_positive"):
            await db.flush()

    async def test_trunk_capacity_non_negative(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        v = _make_vehicle(category_economy, trunk_capacity=-1)
        db.add(v)

        # When/Then
        with pytest.raises(IntegrityError, match="ck_vehicle_trunk_capacity_non_negative"):
            await db.flush()

    async def test_trunk_capacity_zero_allowed(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        v = _make_vehicle(category_economy, trunk_capacity=0)
        db.add(v)

        # When
        await db.flush()

        # Then
        assert v.id is not None

    async def test_license_plate_unique(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        plate = "UNIQUE 001"
        v1 = _make_vehicle(category_economy, license_plate=plate)
        db.add(v1)
        await db.flush()

        v2 = _make_vehicle(category_economy, license_plate=plate)
        db.add(v2)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()

    async def test_vin_unique(self, db: AsyncSession, category_economy):
        # Given
        from tests.integration.conftest import _make_vehicle

        vin = "UNIQUEVIN12345678"[:17]
        v1 = _make_vehicle(category_economy, vin=vin)
        db.add(v1)
        await db.flush()

        v2 = _make_vehicle(category_economy, vin=vin)
        db.add(v2)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()

    async def test_category_name_unique(self, db: AsyncSession):
        # Given
        c1 = Category(name=CategoryName.SUV, price_multiplier=Decimal("1.000"))
        db.add(c1)
        await db.flush()

        c2 = Category(name=CategoryName.SUV, price_multiplier=Decimal("1.100"))
        db.add(c2)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()

    async def test_user_email_unique(self, db: AsyncSession):
        # Given
        u1 = User(
            email="dup@test.com", hashed_password="h", first_name="A", last_name="B"
        )
        db.add(u1)
        await db.flush()

        u2 = User(
            email="dup@test.com", hashed_password="h", first_name="C", last_name="D"
        )
        db.add(u2)

        # When/Then
        with pytest.raises(IntegrityError):
            await db.flush()
