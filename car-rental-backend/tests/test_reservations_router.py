import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.deps import get_current_user
from app.main import app
from app.models.rental import Reservation, ReservationStatus
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle


def _make_user(role: UserRole = UserRole.CUSTOMER) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "u@example.com"
    user.first_name = "U"
    user.last_name = "Ser"
    user.role = role
    user.is_verified = True
    user.is_active = True
    return user


def _make_vehicle() -> MagicMock:
    v = MagicMock(spec=Vehicle)
    v.id = uuid.uuid4()
    v.brand = "Toyota"
    v.model = "Corolla"
    v.year = 2023
    v.license_plate = "ABC1234"
    v.images = []
    return v


def _make_reservation(
    user: MagicMock,
    vehicle: MagicMock,
    status: ReservationStatus = ReservationStatus.PENDING,
) -> MagicMock:
    r = MagicMock(spec=Reservation)
    r.id = uuid.uuid4()
    r.user_id = user.id
    r.vehicle_id = vehicle.id
    r.vehicle = vehicle
    r.start_date = datetime.now(UTC) + timedelta(days=2)
    r.end_date = datetime.now(UTC) + timedelta(days=5)
    r.status = status
    r.total_price = Decimal("450.00")
    r.created_at = datetime.now(UTC)
    return r


class TestCreateReservation:
    async def test_create_success(self, client):
        user = _make_user()
        vehicle = _make_vehicle()
        reservation = _make_reservation(user, vehicle)
        app.dependency_overrides[get_current_user] = lambda: user

        with patch(
            "app.routers.reservations.reservation_service.create_reservation",
            new_callable=AsyncMock,
            return_value=reservation,
        ):
            try:
                resp = await client.post(
                    "/reservations",
                    json={
                        "vehicle_id": str(vehicle.id),
                        "start_date": (datetime.now(UTC).date() + timedelta(days=2)).isoformat(),
                        "end_date": (datetime.now(UTC).date() + timedelta(days=5)).isoformat(),
                    },
                )
            finally:
                app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "pending"
        assert body["total_price"] == "450.00"

    async def test_past_start_date_returns_422(self, client):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.post(
                "/reservations",
                json={
                    "vehicle_id": str(uuid.uuid4()),
                    "start_date": (datetime.now(UTC).date() - timedelta(days=1)).isoformat(),
                    "end_date": (datetime.now(UTC).date() + timedelta(days=2)).isoformat(),
                },
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 422

    async def test_end_before_start_returns_422(self, client):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.post(
                "/reservations",
                json={
                    "vehicle_id": str(uuid.uuid4()),
                    "start_date": (datetime.now(UTC).date() + timedelta(days=5)).isoformat(),
                    "end_date": (datetime.now(UTC).date() + timedelta(days=2)).isoformat(),
                },
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 422

    async def test_unauthenticated_returns_401(self, client):
        resp = await client.post(
            "/reservations",
            json={
                "vehicle_id": str(uuid.uuid4()),
                "start_date": (datetime.now(UTC).date() + timedelta(days=2)).isoformat(),
                "end_date": (datetime.now(UTC).date() + timedelta(days=5)).isoformat(),
            },
        )
        assert resp.status_code == 401


class TestConfirmReservationRBAC:
    """confirm_reservation requires Employee or Admin role."""

    async def test_customer_forbidden(self, client):
        user = _make_user(role=UserRole.CUSTOMER)
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.put(f"/reservations/{uuid.uuid4()}/confirm")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 403

    async def test_employee_allowed(self, client):
        user = _make_user(role=UserRole.EMPLOYEE)
        vehicle = _make_vehicle()
        reservation = _make_reservation(user, vehicle, status=ReservationStatus.CONFIRMED)
        from app.schemas.reservation import ReservationConfirmedEmailData

        email_data = ReservationConfirmedEmailData(
            to_email="cust@example.com",
            first_name="Cust",
            vehicle_name="Toyota Corolla",
            start_date=reservation.start_date.date(),
            end_date=reservation.end_date.date(),
            total_price=Decimal("450.00"),
        )

        app.dependency_overrides[get_current_user] = lambda: user

        with patch(
            "app.routers.reservations.reservation_service.confirm_reservation",
            new_callable=AsyncMock,
            return_value=(reservation, email_data),
        ):
            try:
                resp = await client.put(f"/reservations/{reservation.id}/confirm")
            finally:
                app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"


class TestAdminEndpointsRBAC:
    async def test_customer_cannot_list_admin_reservations(self, client):
        user = _make_user(role=UserRole.CUSTOMER)
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.get("/admin/reservations")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 403

    async def test_employee_cannot_list_admin_users(self, client):
        # admin/users requires ADMIN, not EMPLOYEE
        user = _make_user(role=UserRole.EMPLOYEE)
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.get("/admin/users")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 403
