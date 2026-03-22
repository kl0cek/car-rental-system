import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.category import CategoryName
from app.models.vehicle import EngineType, VehicleStatus
from app.schemas.vehicle import (
    AvailabilityResponse,
    BookedDateRange,
    CategoryResponse,
    PaginatedVehicleResponse,
    VehicleDetailResponse,
    VehicleListItem,
)

VEHICLE_ID = uuid.uuid4()
CATEGORY_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _make_category_response() -> CategoryResponse:
    return CategoryResponse(
        id=CATEGORY_ID,
        name=CategoryName.COMFORT,
        description="Comfort class",
        price_multiplier=Decimal("1.200"),
    )


def _make_vehicle_list_item(**overrides) -> VehicleListItem:
    defaults = dict(
        id=VEHICLE_ID,
        brand="Toyota",
        model="Corolla",
        year=2023,
        engine_type=EngineType.PETROL,
        horsepower=140,
        seats=5,
        trunk_capacity=361,
        daily_base_price=Decimal("150.00"),
        color="White",
        mileage=25000,
        image_url=None,
        status=VehicleStatus.AVAILABLE,
        category=_make_category_response(),
    )
    defaults.update(overrides)
    return VehicleListItem(**defaults)


def _make_paginated_response(items=None, total=1) -> PaginatedVehicleResponse:
    return PaginatedVehicleResponse(
        items=[_make_vehicle_list_item()] if items is None else items,
        total=total,
        offset=0,
        limit=20,
    )


def _make_detail_response(**overrides) -> VehicleDetailResponse:
    defaults = dict(
        id=VEHICLE_ID,
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
        color="White",
        mileage=25000,
        image_url=None,
        status=VehicleStatus.AVAILABLE,
        is_active=True,
        category=_make_category_response(),
        average_rating=4.5,
        review_count=2,
        booked_dates=[],
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(overrides)
    return VehicleDetailResponse(**defaults)


def _make_availability_response(**overrides) -> AvailabilityResponse:
    defaults = dict(
        vehicle_id=VEHICLE_ID,
        available=True,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 5),
        conflicting_rentals=0,
    )
    defaults.update(overrides)
    return AvailabilityResponse(**defaults)



class TestListVehicles:
    @pytest.mark.asyncio
    async def test_list_vehicles_default_params(self, client):
        # Given
        response_data = _make_paginated_response()

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=response_data,
        ):
            resp = await client.get("/vehicles")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["brand"] == "Toyota"

    @pytest.mark.asyncio
    async def test_list_vehicles_with_filters(self, client):
        # Given
        response_data = _make_paginated_response()

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=response_data,
        ) as mock_list:
            resp = await client.get(
                "/vehicles",
                params={
                    "category": "comfort",
                    "engine_type": "diesel",
                    "min_price": "100",
                    "max_price": "500",
                    "min_year": "2020",
                    "max_year": "2025",
                    "min_seats": "4",
                    "status": "available",
                    "sort_by": "daily_base_price",
                    "sort_order": "asc",
                    "offset": "0",
                    "limit": "10",
                },
            )

        # Then
        assert resp.status_code == 200
        mock_list.assert_awaited_once()
        params = mock_list.call_args[0][0]
        assert params.category == CategoryName.COMFORT
        assert params.engine_type == EngineType.DIESEL
        assert params.min_price == Decimal("100")
        assert params.max_price == Decimal("500")
        assert params.min_year == 2020
        assert params.max_year == 2025
        assert params.min_seats == 4
        assert params.sort_by == "daily_base_price"
        assert params.sort_order == "asc"
        assert params.limit == 10

    @pytest.mark.asyncio
    async def test_list_vehicles_with_availability_dates(self, client):
        # Given
        response_data = _make_paginated_response(items=[], total=0)

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=response_data,
        ) as mock_list:
            resp = await client.get(
                "/vehicles",
                params={"available_from": "2026-04-01", "available_to": "2026-04-10"},
            )

        # Then
        assert resp.status_code == 200
        params = mock_list.call_args[0][0]
        assert params.available_from == date(2026, 4, 1)
        assert params.available_to == date(2026, 4, 10)

    @pytest.mark.asyncio
    async def test_list_vehicles_empty_result(self, client):
        # Given
        response_data = _make_paginated_response(items=[], total=0)

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=response_data,
        ):
            resp = await client.get("/vehicles")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_sort_by_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"sort_by": "nonexistent"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_sort_order_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"sort_order": "invalid"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_category_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"category": "luxury"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_engine_type_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"engine_type": "nuclear"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_negative_min_price_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"min_price": "-1"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_limit_too_high_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"limit": "101"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_limit_zero_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"limit": "0"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_negative_offset_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"offset": "-1"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_vehicles_min_price_greater_than_max_price(self, client):
        # When
        resp = await client.get(
            "/vehicles", params={"min_price": "500", "max_price": "100"}
        )

        # Then
        assert resp.status_code == 422
        assert "min_price" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_vehicles_available_from_after_available_to(self, client):
        # When
        resp = await client.get(
            "/vehicles",
            params={"available_from": "2026-04-10", "available_to": "2026-04-01"},
        )

        # Then
        assert resp.status_code == 422
        assert "available_from" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_vehicles_price_exceeds_max_rejected(self, client):
        # When/Then
        resp = await client.get("/vehicles", params={"max_price": "100000000"})
        assert resp.status_code == 422


class TestGetVehicle:
    @pytest.mark.asyncio
    async def test_get_vehicle_success(self, client):
        # Given
        detail = _make_detail_response()

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=detail,
        ):
            resp = await client.get(f"/vehicles/{VEHICLE_ID}")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["brand"] == "Toyota"
        assert data["vin"] == "JTDKN3DU5A0000001"
        assert data["average_rating"] == 4.5
        assert data["review_count"] == 2
        assert data["category"]["name"] == "comfort"

    @pytest.mark.asyncio
    async def test_get_vehicle_with_booked_dates(self, client):
        # Given
        detail = _make_detail_response(
            booked_dates=[
                BookedDateRange(start_date=NOW, end_date=NOW),
            ]
        )

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=detail,
        ):
            resp = await client.get(f"/vehicles/{VEHICLE_ID}")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()["booked_dates"]) == 1

    @pytest.mark.asyncio
    async def test_get_vehicle_no_reviews(self, client):
        # Given
        detail = _make_detail_response(average_rating=None, review_count=0)

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=detail,
        ):
            resp = await client.get(f"/vehicles/{VEHICLE_ID}")

        # Then
        assert resp.status_code == 200
        assert resp.json()["average_rating"] is None
        assert resp.json()["review_count"] == 0

    @pytest.mark.asyncio
    async def test_get_vehicle_not_found(self, client):
        # Given: service returns None

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get(f"/vehicles/{uuid.uuid4()}")

        # Then
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_vehicle_invalid_uuid(self, client):
        # When/Then
        resp = await client.get("/vehicles/not-a-uuid")
        assert resp.status_code == 422


class TestCheckAvailability:
    @pytest.mark.asyncio
    async def test_check_availability_available(self, client):
        # Given
        avail = _make_availability_response(available=True, conflicting_rentals=0)

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=avail,
        ):
            resp = await client.get(
                f"/vehicles/{VEHICLE_ID}/availability",
                params={"start_date": "2026-04-01", "end_date": "2026-04-05"},
            )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["conflicting_rentals"] == 0

    @pytest.mark.asyncio
    async def test_check_availability_unavailable(self, client):
        # Given
        avail = _make_availability_response(available=False, conflicting_rentals=2)

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=avail,
        ):
            resp = await client.get(
                f"/vehicles/{VEHICLE_ID}/availability",
                params={"start_date": "2026-04-01", "end_date": "2026-04-05"},
            )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["conflicting_rentals"] == 2

    @pytest.mark.asyncio
    async def test_check_availability_vehicle_not_found(self, client):
        # Given: service returns None

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get(
                f"/vehicles/{uuid.uuid4()}/availability",
                params={"start_date": "2026-04-01", "end_date": "2026-04-05"},
            )

        # Then
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_check_availability_start_after_end(self, client):
        # When
        resp = await client.get(
            f"/vehicles/{VEHICLE_ID}/availability",
            params={"start_date": "2026-04-10", "end_date": "2026-04-01"},
        )

        # Then
        assert resp.status_code == 422
        assert "start_date" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_check_availability_missing_dates(self, client):
        # When/Then
        resp = await client.get(f"/vehicles/{VEHICLE_ID}/availability")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_check_availability_missing_end_date(self, client):
        # When/Then
        resp = await client.get(
            f"/vehicles/{VEHICLE_ID}/availability",
            params={"start_date": "2026-04-01"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_check_availability_same_day(self, client):
        # Given
        avail = _make_availability_response(
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 1)
        )

        # When
        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=avail,
        ):
            resp = await client.get(
                f"/vehicles/{VEHICLE_ID}/availability",
                params={"start_date": "2026-04-01", "end_date": "2026-04-01"},
            )

        # Then
        assert resp.status_code == 200
