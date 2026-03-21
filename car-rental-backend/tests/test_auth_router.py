import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    return session


@pytest.fixture
async def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        user_id = uuid.uuid4()
        now = datetime.now()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.email = "new@example.com"
        mock_user.first_name = "New"
        mock_user.last_name = "User"
        mock_user.role = UserRole.CUSTOMER
        mock_user.is_verified = False
        mock_user.created_at = now

        with patch(
            "app.routers.auth.register_user",
            new_callable=AsyncMock,
            return_value=(mock_user, "verify-token"),
        ):
            resp = await client.post(
                "/auth/register",
                json={
                    "email": "new@example.com",
                    "password": "securepass123",
                    "first_name": "New",
                    "last_name": "User",
                },
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "customer"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        with patch(
            "app.routers.auth.register_user",
            new_callable=AsyncMock,
            side_effect=EmailAlreadyRegisteredError("dup@example.com"),
        ):
            resp = await client.post(
                "/auth/register",
                json={
                    "email": "dup@example.com",
                    "password": "securepass123",
                    "first_name": "Dup",
                    "last_name": "User",
                },
            )

        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_validation(self, client):
        resp = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert resp.status_code == 422


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            return_value=TokenResponse(access_token="acc", refresh_token="ref"),
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "correct"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "acc"
        assert data["refresh_token"] == "ref"
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            side_effect=InvalidCredentialsError,
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "wrong"},
            )

        assert resp.status_code == 401


class TestRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_refresh_success(self, client):
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            return_value=TokenResponse(access_token="new-acc", refresh_token="new-ref"),
        ):
            resp = await client.post(
                "/auth/refresh",
                json={"refresh_token": "old-refresh"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "new-acc"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client):
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/refresh",
                json={"refresh_token": "bad-token"},
            )

        assert resp.status_code == 401


class TestLogoutEndpoint:
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        with patch(
            "app.routers.auth.logout_user",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/auth/logout",
                json={"access_token": "acc", "refresh_token": "ref"},
            )

        assert resp.status_code == 204
