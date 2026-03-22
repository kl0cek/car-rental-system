"""Integration tests for vehicle_repository against a real PostgreSQL database."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryName
from app.models.rental import Rental, RentalStatus
from app.models.user import User
from app.models.vehicle import EngineType, Vehicle, VehicleStatus
from app.repositories import vehicle_repository

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# get_list — basic & pagination
# ---------------------------------------------------------------------------


class TestGetList:
    async def test_returns_only_active_vehicles(
        self, db: AsyncSession, vehicle, vehicle_inactive
    ):
        # Given: one active and one inactive vehicle

        # When
        vehicles, total = await vehicle_repository.get_list(db)

        # Then
        ids = {v.id for v in vehicles}
        assert vehicle.id in ids
        assert vehicle_inactive.id not in ids
        assert total == 1

    async def test_pagination_offset_limit(
        self, db: AsyncSession, category_economy
    ):
        # Given
        from tests.integration.conftest import _make_vehicle

        for i in range(5):
            db.add(_make_vehicle(category_economy, brand=f"Brand{i}"))
        await db.flush()

        # When
        vehicles, total = await vehicle_repository.get_list(db, offset=2, limit=2)

        # Then
        assert len(vehicles) == 2
        assert total == 5

    async def test_sort_by_price_asc(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles priced at 150 and 300

        # When
        vehicles, _ = await vehicle_repository.get_list(
            db, sort_by="daily_base_price", sort_order="asc"
        )

        # Then
        assert len(vehicles) >= 2
        assert vehicles[0].daily_base_price <= vehicles[1].daily_base_price

    async def test_sort_by_year_desc(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles from 2023 and 2024

        # When
        vehicles, _ = await vehicle_repository.get_list(
            db, sort_by="year", sort_order="desc"
        )

        # Then
        assert vehicles[0].year >= vehicles[1].year


# ---------------------------------------------------------------------------
# get_list — filters
# ---------------------------------------------------------------------------


class TestGetListFilters:
    async def test_filter_by_category(
        self, db: AsyncSession, vehicle, vehicle_comfort, category_comfort
    ):
        # Given: an economy and a comfort vehicle

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, category=CategoryName.COMFORT
        )

        # Then
        assert total == 1
        assert vehicles[0].id == vehicle_comfort.id

    async def test_filter_by_engine_type(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: a petrol and a diesel vehicle

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, engine_type=EngineType.DIESEL
        )

        # Then
        assert total == 1
        assert vehicles[0].engine_type == EngineType.DIESEL

    async def test_filter_by_min_price(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles priced at 150 and 300

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, min_price=Decimal("200")
        )

        # Then
        assert all(v.daily_base_price >= Decimal("200") for v in vehicles)
        assert vehicle_comfort.id in {v.id for v in vehicles}

    async def test_filter_by_max_price(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles priced at 150 and 300

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, max_price=Decimal("200")
        )

        # Then
        assert all(v.daily_base_price <= Decimal("200") for v in vehicles)
        assert vehicle.id in {v.id for v in vehicles}

    async def test_filter_by_price_range(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles priced at 150 and 300

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, min_price=Decimal("100"), max_price=Decimal("200")
        )

        # Then
        assert total == 1
        assert vehicles[0].id == vehicle.id

    async def test_filter_by_year_range(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: vehicles from 2023 and 2024

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, min_year=2024, max_year=2024
        )

        # Then
        assert total == 1
        assert vehicles[0].id == vehicle_comfort.id

    async def test_filter_by_min_seats(
        self, db: AsyncSession, category_economy
    ):
        # Given
        from tests.integration.conftest import _make_vehicle

        db.add(_make_vehicle(category_economy, seats=2))
        db.add(_make_vehicle(category_economy, seats=7))
        await db.flush()

        # When
        vehicles, total = await vehicle_repository.get_list(db, min_seats=5)

        # Then
        assert all(v.seats >= 5 for v in vehicles)

    async def test_filter_by_status(
        self, db: AsyncSession, category_economy
    ):
        # Given
        from tests.integration.conftest import _make_vehicle

        db.add(_make_vehicle(category_economy, status=VehicleStatus.MAINTENANCE))
        await db.flush()

        # When
        vehicles, total = await vehicle_repository.get_list(
            db, status=VehicleStatus.MAINTENANCE
        )

        # Then
        assert total == 1
        assert vehicles[0].status == VehicleStatus.MAINTENANCE

    async def test_combined_filters(
        self, db: AsyncSession, vehicle, vehicle_comfort
    ):
        # Given: economy/petrol/150 vehicle and comfort/diesel/300 vehicle

        # When
        vehicles, total = await vehicle_repository.get_list(
            db,
            category=CategoryName.ECONOMY,
            engine_type=EngineType.PETROL,
            min_price=Decimal("100"),
            max_price=Decimal("200"),
        )

        # Then
        assert total == 1
        assert vehicles[0].id == vehicle.id


# ---------------------------------------------------------------------------
# get_list — availability date filter
# ---------------------------------------------------------------------------


class TestGetListAvailability:
    async def test_excludes_vehicles_with_active_rental(
        self, db: AsyncSession, vehicle, vehicle_comfort, rental_active
    ):
        # Given: vehicle has an active rental, vehicle_comfort is free

        # When
        now = datetime.now(UTC)
        vehicles, total = await vehicle_repository.get_list(
            db,
            available_from=now.date(),
            available_to=(now + timedelta(days=3)).date(),
        )

        # Then
        ids = {v.id for v in vehicles}
        assert vehicle.id not in ids
        assert vehicle_comfort.id in ids

    async def test_includes_vehicle_when_dates_dont_overlap(
        self, db: AsyncSession, vehicle, rental_active
    ):
        # Given: vehicle has an active rental in the current period

        # When
        vehicles, total = await vehicle_repository.get_list(
            db,
            available_from=date(2027, 1, 1),
            available_to=date(2027, 1, 10),
        )

        # Then
        ids = {v.id for v in vehicles}
        assert vehicle.id in ids

    async def test_excludes_pending_rentals(
        self, db: AsyncSession, vehicle, rental_pending_future
    ):
        # Given: vehicle has a pending rental 10-15 days from now

        # When
        now = datetime.now(UTC)
        start = (now + timedelta(days=10)).date()
        end = (now + timedelta(days=12)).date()
        vehicles, total = await vehicle_repository.get_list(
            db, available_from=start, available_to=end
        )

        # Then
        ids = {v.id for v in vehicles}
        assert vehicle.id not in ids


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    async def test_returns_vehicle_with_category(self, db: AsyncSession, vehicle):
        # Given: an active vehicle with economy category

        # When
        result = await vehicle_repository.get_by_id(db, vehicle.id)

        # Then
        assert result is not None
        assert result.id == vehicle.id
        assert result.category is not None
        assert result.category.name == CategoryName.ECONOMY

    async def test_returns_none_for_inactive(
        self, db: AsyncSession, vehicle_inactive
    ):
        # Given: an inactive vehicle

        # When
        result = await vehicle_repository.get_by_id(db, vehicle_inactive.id)

        # Then
        assert result is None

    async def test_returns_none_for_nonexistent(self, db: AsyncSession):
        # Given: a random UUID

        # When
        result = await vehicle_repository.get_by_id(db, uuid.uuid4())

        # Then
        assert result is None


# ---------------------------------------------------------------------------
# count_conflicting_rentals
# ---------------------------------------------------------------------------


class TestCountConflictingRentals:
    async def test_counts_active_conflict(
        self, db: AsyncSession, vehicle, rental_active
    ):
        # Given: vehicle has an active rental overlapping the range

        # When
        now = datetime.now(UTC)
        count = await vehicle_repository.count_conflicting_rentals(
            db, vehicle.id, now.date(), (now + timedelta(days=2)).date()
        )

        # Then
        assert count == 1

    async def test_no_conflict_outside_range(
        self, db: AsyncSession, vehicle, rental_active
    ):
        # Given: vehicle has an active rental in the current period

        # When
        count = await vehicle_repository.count_conflicting_rentals(
            db, vehicle.id, date(2027, 6, 1), date(2027, 6, 10)
        )

        # Then
        assert count == 0

    async def test_counts_pending_as_blocking(
        self, db: AsyncSession, vehicle, rental_pending_future
    ):
        # Given: vehicle has a pending rental 10-15 days from now

        # When
        now = datetime.now(UTC)
        start = (now + timedelta(days=10)).date()
        end = (now + timedelta(days=12)).date()
        count = await vehicle_repository.count_conflicting_rentals(
            db, vehicle.id, start, end
        )

        # Then
        assert count == 1

    async def test_cancelled_rental_not_blocking(
        self, db: AsyncSession, vehicle, user
    ):
        # Given
        now = datetime.now(UTC)
        r = Rental(
            user_id=user.id,
            vehicle_id=vehicle.id,
            start_date=now,
            end_date=now + timedelta(days=3),
            total_price=Decimal("300.00"),
            status=RentalStatus.CANCELLED,
        )
        db.add(r)
        await db.flush()

        # When
        count = await vehicle_repository.count_conflicting_rentals(
            db, vehicle.id, now.date(), (now + timedelta(days=2)).date()
        )

        # Then
        assert count == 0


# ---------------------------------------------------------------------------
# get_booked_dates
# ---------------------------------------------------------------------------


class TestGetBookedDates:
    async def test_returns_future_booked_ranges(
        self, db: AsyncSession, vehicle, rental_active, rental_pending_future
    ):
        # Given: vehicle has active and pending rentals

        # When
        booked = await vehicle_repository.get_booked_dates(db, vehicle.id)

        # Then
        assert len(booked) >= 1
        assert all("start_date" in b and "end_date" in b for b in booked)

    async def test_excludes_past_completed_rentals(
        self, db: AsyncSession, vehicle, user
    ):
        # Given
        past = Rental(
            user_id=user.id,
            vehicle_id=vehicle.id,
            start_date=datetime(2020, 1, 1, tzinfo=UTC),
            end_date=datetime(2020, 1, 5, tzinfo=UTC),
            total_price=Decimal("500.00"),
            status=RentalStatus.COMPLETED,
        )
        db.add(past)
        await db.flush()

        # When
        booked = await vehicle_repository.get_booked_dates(db, vehicle.id)

        # Then
        past_entries = [b for b in booked if b["start_date"].year == 2020]
        assert len(past_entries) == 0

    async def test_empty_for_vehicle_with_no_rentals(
        self, db: AsyncSession, vehicle_comfort
    ):
        # Given: a vehicle with no rentals

        # When
        booked = await vehicle_repository.get_booked_dates(db, vehicle_comfort.id)

        # Then
        assert booked == []

    async def test_ordered_by_start_date(
        self, db: AsyncSession, vehicle, rental_active, rental_pending_future
    ):
        # Given: vehicle has multiple future rentals

        # When
        booked = await vehicle_repository.get_booked_dates(db, vehicle.id)

        # Then
        if len(booked) >= 2:
            assert booked[0]["start_date"] <= booked[1]["start_date"]
