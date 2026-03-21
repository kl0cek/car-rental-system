import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security import create_refresh_token, decode_token
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest
from app.services.auth_service import login_user, logout_user, refresh_tokens, register_user


def _make_user(
    user_id: uuid.UUID | None = None,
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
) -> User:
    user = User(
        email="john@example.com",
        hashed_password="$2b$12$fakehash",
        first_name="John",
        last_name="Doe",
        role=role,
        is_active=is_active,
    )
    user.id = user_id or uuid.uuid4()
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.exists.return_value = 0
    return redis


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_success(self, mock_db, mock_redis):
        body = RegisterRequest(
            email="new@example.com",
            password="securepass123",
            first_name="New",
            last_name="User",
        )

        with (
            patch("app.services.auth_service.user_repository") as mock_repo,
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
        ):
            mock_repo.get_by_email = AsyncMock(return_value=None)
            mock_repo.create = AsyncMock(side_effect=lambda db, u: u)

            user, token = await register_user(body, mock_db)

        assert user.email == "new@example.com"
        assert user.first_name == "New"
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, mock_db):
        body = RegisterRequest(
            email="existing@example.com",
            password="securepass123",
            first_name="Dup",
            last_name="User",
        )
        existing_user = _make_user()

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=existing_user)

            with pytest.raises(EmailAlreadyRegisteredError):
                await register_user(body, mock_db)


class TestLoginUser:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens_with_role(self, mock_db):
        user = _make_user(role=UserRole.EMPLOYEE)
        body = LoginRequest(email="john@example.com", password="correct")

        with patch("app.services.auth_service.user_repository") as mock_repo, patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)

            result = await login_user(body, mock_db)

        access_payload = decode_token(result.access_token)
        refresh_payload = decode_token(result.refresh_token)

        assert access_payload["role"] == "employee"
        assert refresh_payload["role"] == "employee"
        assert access_payload["sub"] == str(user.id)

    @pytest.mark.asyncio
    async def test_login_wrong_email_raises(self, mock_db):
        body = LoginRequest(email="nobody@example.com", password="pass")

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=None)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self, mock_db):
        user = _make_user()
        body = LoginRequest(email="john@example.com", password="wrong")

        with patch("app.services.auth_service.user_repository") as mock_repo, patch(
            "app.services.auth_service.verify_password", return_value=False
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_refresh_success_uses_db_role(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.ADMIN)
        old_refresh = create_refresh_token(str(user.id), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=old_refresh)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            result = await refresh_tokens(body, mock_db)

        new_access_payload = decode_token(result.access_token)
        assert new_access_payload["role"] == "admin"

    @pytest.mark.asyncio
    async def test_refresh_blacklisted_token_raises(self, mock_db, mock_redis):
        mock_redis.exists.return_value = 1
        token = create_refresh_token(str(uuid.uuid4()), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_raises(self, mock_db, mock_redis):
        from app.core.security import create_access_token

        token = create_access_token(str(uuid.uuid4()), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)

    @pytest.mark.asyncio
    async def test_refresh_inactive_user_raises(self, mock_db, mock_redis):
        user = _make_user(is_active=False)
        token = create_refresh_token(str(user.id), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)

    @pytest.mark.asyncio
    async def test_refresh_nonexistent_user_raises(self, mock_db, mock_redis):
        token = create_refresh_token(str(uuid.uuid4()), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)


class TestLogoutUser:
    @pytest.mark.asyncio
    async def test_logout_blacklists_both_tokens(self, mock_redis):
        body = LogoutRequest(access_token="acc-token", refresh_token="ref-token")

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await logout_user(body)

        assert mock_redis.set.await_count == 2
