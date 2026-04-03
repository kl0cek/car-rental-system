import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.deps import get_current_user
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.main import app
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse


def _make_user(
    role: UserRole = UserRole.CUSTOMER,
    is_verified: bool = True,
) -> MagicMock:
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.role = role
    user.is_verified = is_verified
    user.created_at = datetime(2024, 1, 1)
    return user


class TestRegisterEndpoint:
    async def test_register_success(self, client):
        mock_user = _make_user(is_verified=False)

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
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "customer"
        assert "message" in data

    async def test_register_duplicate_email_returns_409(self, client):
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

    async def test_register_short_password_returns_422(self, client):
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

    async def test_register_missing_fields_returns_422(self, client):
        resp = await client.post("/auth/register", json={"email": "x@y.com"})
        assert resp.status_code == 422


class TestLoginEndpoint:
    async def test_login_success_returns_user_profile(self, client):
        mock_user = _make_user()
        tokens = TokenResponse(access_token="acc", refresh_token="ref")

        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            return_value=(tokens, mock_user),
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "correct"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "customer"
        assert "access_token" not in data
        assert "refresh_token" not in data

    async def test_login_success_sets_cookies(self, client):
        mock_user = _make_user()
        tokens = TokenResponse(access_token="acc", refresh_token="ref")

        with patch(
            "app.routers.auth.login_user",
            new_callable=AsyncMock,
            return_value=(tokens, mock_user),
        ):
            resp = await client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "correct"},
            )

        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    async def test_login_invalid_credentials_returns_401(self, client):
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
    async def test_refresh_success_via_cookie(self, client):
        mock_user = _make_user()
        tokens = TokenResponse(access_token="new-acc", refresh_token="new-ref")

        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            return_value=(tokens, mock_user),
        ):
            resp = await client.post(
                "/auth/refresh",
                cookies={"refresh_token": "old-token"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "access_token" not in data

    async def test_refresh_sets_new_cookies(self, client):
        mock_user = _make_user()
        tokens = TokenResponse(access_token="new-acc", refresh_token="new-ref")

        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            return_value=(tokens, mock_user),
        ):
            resp = await client.post(
                "/auth/refresh",
                cookies={"refresh_token": "old-token"},
            )

        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    async def test_refresh_missing_cookie_returns_401(self, client):
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_invalid_token_returns_401(self, client):
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/refresh",
                cookies={"refresh_token": "bad-token"},
            )

        assert resp.status_code == 401

    async def test_refresh_clears_cookies_on_invalid_token(self, client):
        with patch(
            "app.routers.auth.refresh_tokens",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/refresh",
                cookies={"refresh_token": "bad-token"},
            )

        assert resp.status_code == 401
        # Cookies should be cleared (Set-Cookie with empty value / max-age=0)
        set_cookie_headers = resp.headers.get_list("set-cookie")
        cookie_names = [h.split("=")[0] for h in set_cookie_headers]
        assert "access_token" in cookie_names
        assert "refresh_token" in cookie_names


class TestMeEndpoint:
    async def test_returns_current_user_profile(self, client, mock_db):
        mock_user = _make_user(role=UserRole.EMPLOYEE)

        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            resp = await client.get("/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "employee"
        assert data["email"] == "test@example.com"

    async def test_unauthenticated_returns_401(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401


class TestLogoutEndpoint:
    async def test_logout_with_cookies_returns_204(self, client):
        with patch(
            "app.routers.auth.logout_user_tokens",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/auth/logout",
                cookies={"access_token": "acc", "refresh_token": "ref"},
            )

        assert resp.status_code == 204

    async def test_logout_without_cookies_still_returns_204(self, client):
        with patch(
            "app.routers.auth.logout_user_tokens",
            new_callable=AsyncMock,
        ):
            resp = await client.post("/auth/logout")

        assert resp.status_code == 204

    async def test_logout_clears_cookies(self, client):
        with patch(
            "app.routers.auth.logout_user_tokens",
            new_callable=AsyncMock,
        ):
            resp = await client.post(
                "/auth/logout",
                cookies={"access_token": "acc", "refresh_token": "ref"},
            )

        set_cookie_headers = resp.headers.get_list("set-cookie")
        cookie_names = [h.split("=")[0] for h in set_cookie_headers]
        assert "access_token" in cookie_names
        assert "refresh_token" in cookie_names


class TestVerifyEmailEndpoint:
    async def test_success(self, client):
        with patch("app.routers.auth.verify_email", new_callable=AsyncMock):
            resp = await client.get("/auth/verify-email?token=valid-tok")

        assert resp.status_code == 200
        assert resp.json()["message"] == "Email verified successfully"

    async def test_invalid_token_returns_400(self, client):
        with patch(
            "app.routers.auth.verify_email",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.get("/auth/verify-email?token=bad-tok")

        assert resp.status_code == 400

    async def test_missing_token_returns_422(self, client):
        resp = await client.get("/auth/verify-email")
        assert resp.status_code == 422


class TestForgotPasswordEndpoint:
    async def test_existing_user_returns_200_with_message(self, client):
        with patch(
            "app.routers.auth.forgot_password",
            new_callable=AsyncMock,
            return_value="reset-token-123",
        ):
            resp = await client.post(
                "/auth/forgot-password",
                json={"email": "user@example.com"},
            )

        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"]

    async def test_nonexistent_user_returns_same_200(self, client):
        """Anti-enumeration: same response whether user exists or not."""
        with patch(
            "app.routers.auth.forgot_password",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                "/auth/forgot-password",
                json={"email": "nobody@example.com"},
            )

        assert resp.status_code == 200
        assert "reset link" in resp.json()["message"]


class TestResetPasswordEndpoint:
    async def test_success(self, client):
        with patch("app.routers.auth.reset_password", new_callable=AsyncMock):
            resp = await client.post(
                "/auth/reset-password",
                json={"token": "reset-tok", "new_password": "newsecure123"},
            )

        assert resp.status_code == 200
        assert "reset successfully" in resp.json()["message"]

    async def test_invalid_token_returns_400(self, client):
        with patch(
            "app.routers.auth.reset_password",
            new_callable=AsyncMock,
            side_effect=InvalidTokenError,
        ):
            resp = await client.post(
                "/auth/reset-password",
                json={"token": "bad-tok", "new_password": "newsecure123"},
            )

        assert resp.status_code == 400

    async def test_short_password_returns_422(self, client):
        resp = await client.post(
            "/auth/reset-password",
            json={"token": "tok", "new_password": "short"},
        )
        assert resp.status_code == 422
