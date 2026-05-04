import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.core.deps import get_current_user
from app.main import app
from app.models.user import User, UserRole


def _make_user(
    *,
    role: UserRole = UserRole.CUSTOMER,
    created_at: datetime | None = datetime(2024, 1, 1),
    updated_at: datetime | None = datetime(2024, 1, 2),
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "me@example.com"
    user.first_name = "Me"
    user.last_name = "User"
    user.role = role
    user.phone = None
    user.avatar_url = None
    user.risk_score = Decimal("0.00")
    user.is_active = True
    user.is_verified = True
    user.last_login_at = None
    user.created_at = created_at
    user.updated_at = updated_at
    return user


class TestGetMe:
    async def test_returns_user_profile(self, client):
        user = _make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            resp = await client.get("/users/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "me@example.com"
        assert body["role"] == "customer"
        assert body["created_at"] is not None
        assert body["updated_at"] is not None

    async def test_unauthenticated_returns_401(self, client):
        # No dependency override -> get_current_user runs the real path,
        # which fails on missing token.
        resp = await client.get("/users/me")
        assert resp.status_code == 401

    async def test_regression_user_with_no_dates_fails_validation(self, client):
        """Regression for the cache bug: user retrieved from Redis without
        created_at/updated_at must NOT silently round-trip — the response
        schema requires datetimes, so pydantic raises during serialization.

        Pins the contract of UserProfileResponse: created_at/updated_at are
        non-optional. If someone makes them Optional in the schema this test
        breaks — forcing a deliberate decision rather than silent drift.
        """
        import pydantic_core

        user = _make_user(created_at=None, updated_at=None)
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            raised = False
            try:
                await client.get("/users/me")
            except pydantic_core.ValidationError:
                raised = True
            assert raised, (
                "Expected ValidationError when serializing user with None timestamps "
                "(UserProfileResponse must keep created_at/updated_at non-optional)."
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)
