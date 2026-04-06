import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

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


def _make_category() -> CategoryResponse:
    return CategoryResponse(
        id=uuid.uuid4(),
        name=CategoryName.COMFORT,
        description="Comfortable cars",
        price_multiplier=Decimal("1.200"),
    )


def _make_vehicle_list_item() -> VehicleListItem:
    return VehicleListItem(
        id=uuid.uuid4(),
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
        category=_make_category(),
    )


def _make_vehicle_detail(vehicle_id: uuid.UUID | None = None) -> VehicleDetailResponse:
    return VehicleDetailResponse(
        id=vehicle_id or uuid.uuid4(),
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
        is_active=True,
        category=_make_category(),
        average_rating=4.5,
        review_count=10,
        booked_dates=[
            BookedDateRange(
                start_date=datetime(2024, 6, 1),
                end_date=datetime(2024, 6, 5),
            )
        ],
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )


class TestListVehicles:
    async def test_returns_paginated_list(self, client):
        vehicle = _make_vehicle_list_item()
        paginated = PaginatedVehicleResponse(items=[vehicle], total=1, offset=0, limit=20)

        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=paginated,
        ):
            resp = await client.get("/vehicles")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["brand"] == "Toyota"

    async def test_pagination_params_forwarded(self, client):
        paginated = PaginatedVehicleResponse(items=[], total=0, offset=40, limit=10)

        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=paginated,
        ) as mock_svc:
            resp = await client.get("/vehicles?offset=40&limit=10")

        assert resp.status_code == 200
        call_params = mock_svc.call_args[0][0]
        assert call_params.offset == 40
        assert call_params.limit == 10

    async def test_invalid_available_date_range_returns_422(self, client):
        resp = await client.get("/vehicles?available_from=2024-06-10&available_to=2024-06-01")
        assert resp.status_code == 422

    async def test_invalid_price_range_returns_422(self, client):
        resp = await client.get("/vehicles?min_price=500&max_price=100")
        assert resp.status_code == 422

    async def test_invalid_year_range_returns_422(self, client):
        resp = await client.get("/vehicles?min_year=2025&max_year=2020")
        assert resp.status_code == 422

    async def test_invalid_limit_returns_422(self, client):
        resp = await client.get("/vehicles?limit=0")
        assert resp.status_code == 422

    async def test_invalid_offset_returns_422(self, client):
        resp = await client.get("/vehicles?offset=-1")
        assert resp.status_code == 422

    async def test_filters_forwarded_to_service(self, client):
        paginated = PaginatedVehicleResponse(items=[], total=0, offset=0, limit=20)

        with patch(
            "app.routers.vehicles.vehicle_service.list_vehicles",
            new_callable=AsyncMock,
            return_value=paginated,
        ) as mock_svc:
            await client.get("/vehicles?engine_type=electric&min_seats=4&category=suv")

        call_params = mock_svc.call_args[0][0]
        assert call_params.engine_type == EngineType.ELECTRIC
        assert call_params.min_seats == 4
        assert call_params.category == CategoryName.SUV


class TestGetVehicle:
    async def test_returns_vehicle_detail(self, client):
        vehicle_id = uuid.uuid4()
        detail = _make_vehicle_detail(vehicle_id)

        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=detail,
        ):
            resp = await client.get(f"/vehicles/{vehicle_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(vehicle_id)
        assert data["brand"] == "Toyota"
        assert data["average_rating"] == 4.5
        assert len(data["booked_dates"]) == 1

    async def test_detail_excludes_vin_and_license_plate(self, client):
        vehicle_id = uuid.uuid4()
        detail = _make_vehicle_detail(vehicle_id)

        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=detail,
        ):
            resp = await client.get(f"/vehicles/{vehicle_id}")

        data = resp.json()
        assert "vin" not in data
        assert "license_plate" not in data

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.routers.vehicles.vehicle_service.get_vehicle_detail",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get(f"/vehicles/{uuid.uuid4()}")

        assert resp.status_code == 404

    async def test_invalid_uuid_returns_422(self, client):
        resp = await client.get("/vehicles/not-a-uuid")
        assert resp.status_code == 422


class TestCheckAvailability:
    async def test_available_vehicle(self, client):
        vehicle_id = uuid.uuid4()
        result = AvailabilityResponse(
            vehicle_id=vehicle_id,
            available=True,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 5),
            conflicting_rentals=0,
        )

        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = await client.get(
                f"/vehicles/{vehicle_id}/availability",
                params={"start_date": "2024-07-01", "end_date": "2024-07-05"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["conflicting_rentals"] == 0

    async def test_unavailable_vehicle(self, client):
        vehicle_id = uuid.uuid4()
        result = AvailabilityResponse(
            vehicle_id=vehicle_id,
            available=False,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 5),
            conflicting_rentals=2,
        )

        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = await client.get(
                f"/vehicles/{vehicle_id}/availability",
                params={"start_date": "2024-07-01", "end_date": "2024-07-05"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["conflicting_rentals"] == 2

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.routers.vehicles.vehicle_service.check_availability",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.get(
                f"/vehicles/{uuid.uuid4()}/availability",
                params={"start_date": "2024-07-01", "end_date": "2024-07-05"},
            )

        assert resp.status_code == 404

    async def test_invalid_date_range_returns_422(self, client):
        resp = await client.get(
            f"/vehicles/{uuid.uuid4()}/availability",
            params={"start_date": "2024-07-10", "end_date": "2024-07-01"},
        )
        assert resp.status_code == 422

    async def test_missing_dates_returns_422(self, client):
        resp = await client.get(f"/vehicles/{uuid.uuid4()}/availability")
        assert resp.status_code == 422
