import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.category import CategoryName
from app.models.vehicle import EngineType, Vehicle, VehicleStatus
from app.schemas.vehicle import AvailabilityRequest, VehicleListParams
from app.services.vehicle_service import (
    _get_review_stats,
    check_availability,
    get_vehicle_detail,
    list_vehicles,
)

VEHICLE_ID = uuid.uuid4()
CATEGORY_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _make_mock_category() -> MagicMock:
    cat = MagicMock()
    cat.id = CATEGORY_ID
    cat.name = CategoryName.COMFORT
    cat.description = "Comfort class"
    cat.price_multiplier = Decimal("1.200")
    return cat


def _make_mock_vehicle(**overrides) -> MagicMock:
    vehicle = MagicMock(spec=Vehicle)
    vehicle.id = overrides.get("id", VEHICLE_ID)
    vehicle.brand = overrides.get("brand", "Toyota")
    vehicle.model = overrides.get("model", "Corolla")
    vehicle.year = overrides.get("year", 2023)
    vehicle.license_plate = overrides.get("license_plate", "WA 12345")
    vehicle.vin = overrides.get("vin", "JTDKN3DU5A0000001")
    vehicle.engine_type = overrides.get("engine_type", EngineType.PETROL)
    vehicle.horsepower = overrides.get("horsepower", 140)
    vehicle.seats = overrides.get("seats", 5)
    vehicle.trunk_capacity = overrides.get("trunk_capacity", 361)
    vehicle.daily_base_price = overrides.get("daily_base_price", Decimal("150.00"))
    vehicle.color = overrides.get("color", "White")
    vehicle.mileage = overrides.get("mileage", 25000)
    vehicle.image_url = overrides.get("image_url", None)
    vehicle.status = overrides.get("status", VehicleStatus.AVAILABLE)
    vehicle.is_active = overrides.get("is_active", True)
    vehicle.category = overrides.get("category", _make_mock_category())
    vehicle.category_id = overrides.get("category_id", CATEGORY_ID)
    vehicle.created_at = overrides.get("created_at", NOW)
    vehicle.updated_at = overrides.get("updated_at", NOW)
    return vehicle


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestListVehicles:
    @pytest.mark.asyncio
    async def test_returns_paginated_response(self, mock_db):
        # Given
        vehicles = [_make_mock_vehicle(), _make_mock_vehicle(id=uuid.uuid4(), brand="BMW")]
        params = VehicleListParams()

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_list = AsyncMock(return_value=(vehicles, 2))
            result = await list_vehicles(params, mock_db)

        # Then
        assert result.total == 2
        assert len(result.items) == 2
        assert result.offset == 0
        assert result.limit == 20

    @pytest.mark.asyncio
    async def test_passes_all_params_to_repository(self, mock_db):
        # Given
        params = VehicleListParams(
            offset=10,
            limit=5,
            sort_by="brand",
            sort_order="asc",
            category=CategoryName.PREMIUM,
            engine_type=EngineType.ELECTRIC,
            min_price=Decimal("100"),
            max_price=Decimal("500"),
            min_year=2020,
            max_year=2025,
            min_seats=4,
            status=VehicleStatus.AVAILABLE,
            available_from=date(2026, 4, 1),
            available_to=date(2026, 4, 10),
        )

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_list = AsyncMock(return_value=([], 0))
            await list_vehicles(params, mock_db)

        # Then
        mock_repo.get_list.assert_awaited_once_with(
            mock_db,
            offset=10,
            limit=5,
            sort_by="brand",
            sort_order="asc",
            category=CategoryName.PREMIUM,
            engine_type=EngineType.ELECTRIC,
            min_price=Decimal("100"),
            max_price=Decimal("500"),
            min_year=2020,
            max_year=2025,
            min_seats=4,
            status=VehicleStatus.AVAILABLE,
            available_from=date(2026, 4, 1),
            available_to=date(2026, 4, 10),
        )

    @pytest.mark.asyncio
    async def test_empty_result(self, mock_db):
        # Given
        params = VehicleListParams()

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_list = AsyncMock(return_value=([], 0))
            result = await list_vehicles(params, mock_db)

        # Then
        assert result.total == 0
        assert result.items == []


class TestGetVehicleDetail:
    @pytest.mark.asyncio
    async def test_returns_detail_with_reviews_and_booked_dates(self, mock_db):
        # Given
        vehicle = _make_mock_vehicle()
        booked = [
            {"start_date": NOW, "end_date": NOW},
        ]

        # When
        with (
            patch("app.services.vehicle_service.vehicle_repository") as mock_repo,
            patch(
                "app.services.vehicle_service._get_review_stats",
                new_callable=AsyncMock,
            ) as mock_reviews,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=vehicle)
            mock_repo.get_booked_dates = AsyncMock(return_value=booked)
            mock_reviews.return_value = (4.5, 3)
            result = await get_vehicle_detail(VEHICLE_ID, mock_db)

        # Then
        assert result is not None
        assert result.brand == "Toyota"
        assert result.average_rating == 4.5
        assert result.review_count == 3
        assert len(result.booked_dates) == 1
        mock_repo.get_by_id.assert_awaited_once_with(mock_db, VEHICLE_ID)
        mock_repo.get_booked_dates.assert_awaited_once_with(mock_db, VEHICLE_ID)

    @pytest.mark.asyncio
    async def test_returns_none_when_vehicle_not_found(self, mock_db):
        # Given: repository returns None

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await get_vehicle_detail(uuid.uuid4(), mock_db)

        # Then
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_null_rating_when_no_reviews(self, mock_db):
        # Given
        vehicle = _make_mock_vehicle()

        # When
        with (
            patch("app.services.vehicle_service.vehicle_repository") as mock_repo,
            patch(
                "app.services.vehicle_service._get_review_stats",
                new_callable=AsyncMock,
            ) as mock_reviews,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=vehicle)
            mock_repo.get_booked_dates = AsyncMock(return_value=[])
            mock_reviews.return_value = (None, 0)
            result = await get_vehicle_detail(VEHICLE_ID, mock_db)

        # Then
        assert result is not None
        assert result.average_rating is None
        assert result.review_count == 0

    @pytest.mark.asyncio
    async def test_does_not_fetch_reviews_if_vehicle_not_found(self, mock_db):
        # Given: repository returns None

        # When
        with (
            patch("app.services.vehicle_service.vehicle_repository") as mock_repo,
            patch(
                "app.services.vehicle_service._get_review_stats",
                new_callable=AsyncMock,
            ) as mock_reviews,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=None)
            await get_vehicle_detail(uuid.uuid4(), mock_db)

        # Then
        mock_reviews.assert_not_awaited()


class TestCheckAvailability:
    @pytest.mark.asyncio
    async def test_available_when_no_conflicts(self, mock_db):
        # Given
        vehicle = _make_mock_vehicle()
        body = AvailabilityRequest(start_date=date(2026, 4, 1), end_date=date(2026, 4, 5))

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=vehicle)
            mock_repo.count_conflicting_rentals = AsyncMock(return_value=0)
            result = await check_availability(VEHICLE_ID, body, mock_db)

        # Then
        assert result is not None
        assert result.available is True
        assert result.conflicting_rentals == 0
        assert result.vehicle_id == VEHICLE_ID
        assert result.start_date == date(2026, 4, 1)
        assert result.end_date == date(2026, 4, 5)

    @pytest.mark.asyncio
    async def test_unavailable_when_conflicts_exist(self, mock_db):
        # Given
        vehicle = _make_mock_vehicle()
        body = AvailabilityRequest(start_date=date(2026, 4, 1), end_date=date(2026, 4, 5))

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=vehicle)
            mock_repo.count_conflicting_rentals = AsyncMock(return_value=2)
            result = await check_availability(VEHICLE_ID, body, mock_db)

        # Then
        assert result is not None
        assert result.available is False
        assert result.conflicting_rentals == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_vehicle_not_found(self, mock_db):
        # Given
        body = AvailabilityRequest(start_date=date(2026, 4, 1), end_date=date(2026, 4, 5))

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)
            result = await check_availability(uuid.uuid4(), body, mock_db)

        # Then
        assert result is None

    @pytest.mark.asyncio
    async def test_passes_correct_dates_to_repository(self, mock_db):
        # Given
        vehicle = _make_mock_vehicle()
        body = AvailabilityRequest(start_date=date(2026, 5, 10), end_date=date(2026, 5, 20))

        # When
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=vehicle)
            mock_repo.count_conflicting_rentals = AsyncMock(return_value=0)
            await check_availability(VEHICLE_ID, body, mock_db)

        # Then
        mock_repo.count_conflicting_rentals.assert_awaited_once_with(
            mock_db, VEHICLE_ID, date(2026, 5, 10), date(2026, 5, 20)
        )


def _mock_mongo_reviews(results: list) -> MagicMock:
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=results)
    mock_collection = MagicMock()
    mock_collection.aggregate.return_value = mock_cursor
    mock_mongo_db = MagicMock()
    mock_mongo_db.reviews = mock_collection
    return mock_mongo_db


class TestGetReviewStats:
    @pytest.mark.asyncio
    async def test_returns_average_and_count(self):
        # Given
        mock_mongo_db = _mock_mongo_reviews([{"avg": 4.333, "count": 3}])

        # When
        with patch("app.services.vehicle_service.get_mongo_db", return_value=mock_mongo_db):
            avg, count = await _get_review_stats(VEHICLE_ID)

        # Then
        assert avg == 4.33
        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_none_and_zero_when_no_reviews(self):
        # Given
        mock_mongo_db = _mock_mongo_reviews([])

        # When
        with patch("app.services.vehicle_service.get_mongo_db", return_value=mock_mongo_db):
            avg, count = await _get_review_stats(VEHICLE_ID)

        # Then
        assert avg is None
        assert count == 0

    @pytest.mark.asyncio
    async def test_rounds_average_to_two_decimals(self):
        # Given
        mock_mongo_db = _mock_mongo_reviews([{"avg": 3.6667, "count": 3}])

        # When
        with patch("app.services.vehicle_service.get_mongo_db", return_value=mock_mongo_db):
            avg, count = await _get_review_stats(VEHICLE_ID)

        # Then
        assert avg == 3.67

    @pytest.mark.asyncio
    async def test_passes_correct_vehicle_id_to_pipeline(self):
        # Given
        vid = uuid.uuid4()
        mock_mongo_db = _mock_mongo_reviews([])

        # When
        with patch("app.services.vehicle_service.get_mongo_db", return_value=mock_mongo_db):
            await _get_review_stats(vid)

        # Then
        pipeline = mock_mongo_db.reviews.aggregate.call_args[0][0]
        assert pipeline[0]["$match"]["vehicle_id"] == str(vid)
