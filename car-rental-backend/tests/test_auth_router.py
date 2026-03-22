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
        # Given
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

        # When
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

        # Then
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "customer"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        # When
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

        # Then
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_validation(self, client):
        # When/Then
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
        # When
        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            return_value=TokenResponse(access_token="acc", refresh_token="ref"),
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "correct"},
            )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "acc"
        assert data["refresh_token"] == "ref"
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        # When
        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            side_effect=InvalidCredentialsError,
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "wrong"},
            )

        # Then
        assert resp.status_code == 401


class TestRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_refresh_success(self, client):
        # When
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            return_value=TokenResponse(access_token="new-acc", refresh_token="new-ref"),
        ):
            resp = await client.post(
                "/auth/refresh",
                json={"refresh_token": "old-refresh"},
            )

        # Then
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "new-acc"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client):
        # When
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/refresh",
                json={"refresh_token": "bad-token"},
            )

        # Then
        assert resp.status_code == 401


class TestLogoutEndpoint:
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        # When
        with patch(
            "app.routers.auth.logout_user",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/auth/logout",
                json={"access_token": "acc", "refresh_token": "ref"},
            )

        # Then
        assert resp.status_code == 204


class TestVerifyEmailEndpoint:
    @pytest.mark.asyncio
    async def test_verify_email_success(self, client):
        # When
        with patch(
            "app.routers.auth.verify_email",
            new_callable=AsyncMock,
        ):
            resp = await client.get("/auth/verify-email?token=valid-tok")

        # Then
        assert resp.status_code == 200
        assert resp.json()["message"] == "Email verified successfully"

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client):
        # When
        with patch(
            "app.routers.auth.verify_email",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.get("/auth/verify-email?token=bad-tok")

        # Then
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email_missing_token(self, client):
        # When/Then
        resp = await client.get("/auth/verify-email")
        assert resp.status_code == 422


class TestForgotPasswordEndpoint:
    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, client):
        # When
        with patch(
            "app.routers.auth.forgot_password",
            new_callable=AsyncMock,
            return_value="reset-token-123",
        ):
            resp = await client.post(
                "/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        # Then
        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user_same_response(self, client):
        # When
        with patch(
            "app.routers.auth.forgot_password",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                "/auth/forgot-password",
                json={"email": "nobody@example.com"},
            )

        # Then
        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"]


class TestResetPasswordEndpoint:
    @pytest.mark.asyncio
    async def test_reset_password_success(self, client):
        # When
        with patch(
            "app.routers.auth.reset_password",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/auth/reset-password",
                json={"token": "reset-tok", "new_password": "newsecure123"},
            )

        # Then
        assert resp.status_code == 200
        assert "reset successfully" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client):
        # When
        with patch(
            "app.routers.auth.reset_password",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/reset-password",
                json={"token": "bad-tok", "new_password": "newsecure123"},
            )

        # Then
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_short_password_validation(self, client):
        # When/Then
        resp = await client.post(
            "/auth/reset-password",
            json={"token": "tok", "new_password": "short"},
        )
        assert resp.status_code == 422
