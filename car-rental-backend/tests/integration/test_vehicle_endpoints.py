"""Full endpoint integration tests — request → router → service → repository → PostgreSQL."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryName
from app.models.rental import Rental, RentalStatus
from app.models.user import User
from app.models.vehicle import EngineType, Vehicle, VehicleStatus

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# GET /vehicles — list
# ---------------------------------------------------------------------------


class TestListVehiclesEndpoint:
    async def test_returns_vehicles_from_db(self, client, vehicle, vehicle_comfort):
        # Given: two active vehicles (Toyota, BMW)

        # When
        resp = await client.get("/vehicles")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        brands = {item["brand"] for item in data["items"]}
        assert "Toyota" in brands
        assert "BMW" in brands

    async def test_pagination(self, client, vehicle, vehicle_comfort):
        # Given: at least 2 vehicles

        # When
        resp = await client.get("/vehicles", params={"limit": 1, "offset": 0})

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["total"] >= 2

    async def test_filter_by_category(self, client, vehicle, vehicle_comfort):
        # Given: an economy and a comfort vehicle

        # When
        resp = await client.get("/vehicles", params={"category": "comfort"})

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert all(
            item["category"]["name"] == "comfort" for item in data["items"]
        )

    async def test_filter_by_engine_type(self, client, vehicle, vehicle_comfort):
        # Given: a petrol and a diesel vehicle

        # When
        resp = await client.get("/vehicles", params={"engine_type": "diesel"})

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["engine_type"] == "diesel" for item in data["items"])

    async def test_filter_by_price_range(self, client, vehicle, vehicle_comfort):
        # Given: vehicles priced at 150 and 300

        # When
        resp = await client.get(
            "/vehicles", params={"min_price": "200", "max_price": "400"}
        )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            price = Decimal(item["daily_base_price"])
            assert Decimal("200") <= price <= Decimal("400")

    async def test_sort_by_price_asc(self, client, vehicle, vehicle_comfort):
        # Given: vehicles with different prices

        # When
        resp = await client.get(
            "/vehicles",
            params={"sort_by": "daily_base_price", "sort_order": "asc"},
        )

        # Then
        assert resp.status_code == 200
        items = resp.json()["items"]
        prices = [Decimal(i["daily_base_price"]) for i in items]
        assert prices == sorted(prices)

    async def test_excludes_inactive_vehicles(self, client, vehicle, vehicle_inactive):
        # Given: one active and one inactive vehicle

        # When
        resp = await client.get("/vehicles")

        # Then
        assert resp.status_code == 200
        ids = {item["id"] for item in resp.json()["items"]}
        assert str(vehicle_inactive.id) not in ids

    async def test_availability_date_filter(
        self, client, vehicle, vehicle_comfort, rental_active
    ):
        # Given: vehicle has an active rental, vehicle_comfort is free

        # When
        now = datetime.now(UTC)
        resp = await client.get(
            "/vehicles",
            params={
                "available_from": now.date().isoformat(),
                "available_to": (now + timedelta(days=3)).date().isoformat(),
            },
        )

        # Then
        assert resp.status_code == 200
        ids = {item["id"] for item in resp.json()["items"]}
        assert str(vehicle.id) not in ids
        assert str(vehicle_comfort.id) in ids

    async def test_category_in_response(self, client, vehicle):
        # Given: a vehicle with a category

        # When
        resp = await client.get("/vehicles")

        # Then
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert "category" in item
        assert "name" in item["category"]
        assert "price_multiplier" in item["category"]


# ---------------------------------------------------------------------------
# GET /vehicles/{id} — detail
# ---------------------------------------------------------------------------


class TestGetVehicleEndpoint:
    async def test_returns_vehicle_detail(self, client, vehicle):
        # Given: an active vehicle with mocked review stats
        with patch(
            "app.services.vehicle_service._get_review_stats",
            new_callable=AsyncMock,
            return_value=(4.5, 10),
        ):
            # When
            resp = await client.get(f"/vehicles/{vehicle.id}")

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(vehicle.id)
        assert data["brand"] == "Toyota"
        assert data["vin"] is not None
        assert data["license_plate"] is not None
        assert data["average_rating"] == 4.5
        assert data["review_count"] == 10
        assert "booked_dates" in data
        assert "category" in data

    async def test_includes_booked_dates(self, client, vehicle, rental_active):
        # Given: a vehicle with an active rental
        with patch(
            "app.services.vehicle_service._get_review_stats",
            new_callable=AsyncMock,
            return_value=(None, 0),
        ):
            # When
            resp = await client.get(f"/vehicles/{vehicle.id}")

        # Then
        assert resp.status_code == 200
        assert len(resp.json()["booked_dates"]) >= 1

    async def test_404_for_nonexistent(self, client):
        # Given: a random UUID
        with patch(
            "app.services.vehicle_service._get_review_stats",
            new_callable=AsyncMock,
            return_value=(None, 0),
        ):
            # When
            resp = await client.get(f"/vehicles/{uuid.uuid4()}")

        # Then
        assert resp.status_code == 404

    async def test_404_for_inactive(self, client, vehicle_inactive):
        # Given: an inactive vehicle
        with patch(
            "app.services.vehicle_service._get_review_stats",
            new_callable=AsyncMock,
            return_value=(None, 0),
        ):
            # When
            resp = await client.get(f"/vehicles/{vehicle_inactive.id}")

        # Then
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /vehicles/{id}/availability
# ---------------------------------------------------------------------------


class TestCheckAvailabilityEndpoint:
    async def test_available_when_no_rentals(self, client, vehicle_comfort):
        # Given: a vehicle with no rentals

        # When
        resp = await client.get(
            f"/vehicles/{vehicle_comfort.id}/availability",
            params={"start_date": "2026-06-01", "end_date": "2026-06-10"},
        )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["conflicting_rentals"] == 0
        assert data["vehicle_id"] == str(vehicle_comfort.id)

    async def test_unavailable_when_rental_conflicts(
        self, client, vehicle, rental_active
    ):
        # Given: a vehicle with an active rental

        # When
        now = datetime.now(UTC)
        resp = await client.get(
            f"/vehicles/{vehicle.id}/availability",
            params={
                "start_date": now.date().isoformat(),
                "end_date": (now + timedelta(days=2)).date().isoformat(),
            },
        )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["conflicting_rentals"] >= 1

    async def test_404_for_nonexistent_vehicle(self, client):
        # Given: a random UUID

        # When
        resp = await client.get(
            f"/vehicles/{uuid.uuid4()}/availability",
            params={"start_date": "2026-06-01", "end_date": "2026-06-10"},
        )

        # Then
        assert resp.status_code == 404

    async def test_422_start_after_end(self, client, vehicle):
        # Given: a valid vehicle

        # When
        resp = await client.get(
            f"/vehicles/{vehicle.id}/availability",
            params={"start_date": "2026-06-10", "end_date": "2026-06-01"},
        )

        # Then
        assert resp.status_code == 422

    async def test_same_day_allowed(self, client, vehicle_comfort):
        # Given: a vehicle with no rentals

        # When
        resp = await client.get(
            f"/vehicles/{vehicle_comfort.id}/availability",
            params={"start_date": "2026-06-01", "end_date": "2026-06-01"},
        )

        # Then
        assert resp.status_code == 200
        assert resp.json()["available"] is True
