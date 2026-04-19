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
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    forgot_password,
    login_user,
    logout_user_tokens,
    refresh_tokens,
    register_user,
    reset_password,
    verify_email,
)


def _make_user(
    user_id: uuid.UUID | None = None,
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    user = User(
        email="john@example.com",
        hashed_password="$2b$12$fakehash",
        first_name="John",
        last_name="Doe",
        role=role,
        is_active=is_active,
        is_verified=is_verified,
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

    async def test_register_duplicate_email_raises(self, mock_db):
        body = RegisterRequest(
            email="existing@example.com",
            password="securepass123",
            first_name="Dup",
            last_name="User",
        )

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=_make_user())

            with pytest.raises(EmailAlreadyRegisteredError):
                await register_user(body, mock_db)


class TestLoginUser:
    async def test_login_success_returns_tokens_and_user(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.EMPLOYEE)
        body = LoginRequest(email="john@example.com", password="correct")

        with (
            patch("app.services.auth_service.user_repository") as mock_repo,
            patch("app.services.auth_service.verify_password", return_value=True),
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)
            mock_repo.update_last_login = AsyncMock(return_value=user)

            tokens, returned_user = await login_user(body, mock_db)

        access_payload = decode_token(tokens.access_token)
        refresh_payload = decode_token(tokens.refresh_token)

        assert access_payload["role"] == "employee"
        assert refresh_payload["role"] == "employee"
        assert access_payload["sub"] == str(user.id)
        assert returned_user is user

    async def test_login_wrong_email_raises(self, mock_db):
        body = LoginRequest(email="nobody@example.com", password="pass")

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=None)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

    async def test_login_wrong_password_raises(self, mock_db):
        user = _make_user()
        body = LoginRequest(email="john@example.com", password="wrong")

        with (
            patch("app.services.auth_service.user_repository") as mock_repo,
            patch("app.services.auth_service.verify_password", return_value=False),
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

    async def test_login_inactive_user_raises(self, mock_db):
        user = _make_user(is_active=False)
        body = LoginRequest(email="john@example.com", password="correct")

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=user)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

    async def test_login_unverified_user_raises(self, mock_db):
        user = _make_user(is_verified=False)
        body = LoginRequest(email="john@example.com", password="correct")

        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=user)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

    async def test_inactive_checked_before_password_verify(self, mock_db):
        """is_active/is_verified should be checked before the bcrypt call."""
        user = _make_user(is_active=False)
        body = LoginRequest(email="john@example.com", password="correct")

        with (
            patch("app.services.auth_service.user_repository") as mock_repo,
            patch("app.services.auth_service.verify_password") as mock_verify,
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)

            with pytest.raises(InvalidCredentialsError):
                await login_user(body, mock_db)

        mock_verify.assert_not_called()


class TestRefreshTokens:
    async def test_refresh_success_returns_tokens_and_user(self, mock_db, mock_redis):
        user = _make_user(role=UserRole.ADMIN)
        old_refresh = create_refresh_token(str(user.id), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=old_refresh)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)

            tokens, returned_user = await refresh_tokens(body, mock_db)

        new_access_payload = decode_token(tokens.access_token)
        assert new_access_payload["role"] == "admin"
        assert returned_user is user

    async def test_refresh_blacklisted_token_raises(self, mock_db, mock_redis):
        mock_redis.exists.return_value = 1
        token = create_refresh_token(str(uuid.uuid4()), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)

    async def test_refresh_with_access_token_raises(self, mock_db, mock_redis):
        from app.core.security import create_access_token

        token = create_access_token(str(uuid.uuid4()), UserRole.CUSTOMER)
        body = RefreshRequest(refresh_token=token)

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            with pytest.raises(InvalidTokenError):
                await refresh_tokens(body, mock_db)

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


class TestLogoutUserTokens:
    async def test_blacklists_both_tokens(self, mock_redis):
        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await logout_user_tokens("acc-token", "ref-token")

        assert mock_redis.set.await_count == 2

    async def test_blacklists_only_access_when_refresh_missing(self, mock_redis):
        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await logout_user_tokens("acc-token", None)

        assert mock_redis.set.await_count == 1

    async def test_blacklists_only_refresh_when_access_missing(self, mock_redis):
        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await logout_user_tokens(None, "ref-token")

        assert mock_redis.set.await_count == 1

    async def test_no_blacklist_when_both_missing(self, mock_redis):
        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            await logout_user_tokens(None, None)

        mock_redis.set.assert_not_awaited()


class TestVerifyEmail:
    async def test_verify_email_success(self, mock_db, mock_redis):
        user = _make_user(is_verified=False)
        mock_redis.getdel.return_value = str(user.id)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)
            mock_repo.update = AsyncMock(return_value=user)

            await verify_email("valid-token", mock_db)

        assert user.is_verified is True
        mock_redis.getdel.assert_awaited_once_with("verify:valid-token")

    async def test_verify_email_already_verified_skips_update(self, mock_db, mock_redis):
        user = _make_user()
        user.is_verified = True
        mock_redis.getdel.return_value = str(user.id)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)
            mock_repo.update = AsyncMock()

            await verify_email("valid-token", mock_db)

        mock_repo.update.assert_not_awaited()

    async def test_verify_email_invalid_token_raises(self, mock_db, mock_redis):
        mock_redis.getdel.return_value = None

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            with pytest.raises(InvalidTokenError):
                await verify_email("bad-token", mock_db)

    async def test_verify_email_user_not_found_raises(self, mock_db, mock_redis):
        mock_redis.getdel.return_value = str(uuid.uuid4())

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(InvalidTokenError):
                await verify_email("orphan-token", mock_db)


class TestForgotPassword:
    async def test_existing_user_returns_token(self, mock_db, mock_redis):
        user = _make_user()

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)
            body = ForgotPasswordRequest(email="john@example.com")

            token = await forgot_password(body, mock_db)

        assert token is not None
        assert len(token) > 0
        set_keys = [call.args[0] for call in mock_redis.set.call_args_list]
        assert any(k.startswith("reset:") for k in set_keys)
        assert any(k.startswith("reset_cooldown:") for k in set_keys)

    async def test_nonexistent_user_returns_none(self, mock_db):
        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=None)
            body = ForgotPasswordRequest(email="nobody@example.com")

            token = await forgot_password(body, mock_db)

        assert token is None

    async def test_cooldown_returns_none(self, mock_db, mock_redis):
        user = _make_user()
        mock_redis.exists.return_value = 1

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_email = AsyncMock(return_value=user)
            body = ForgotPasswordRequest(email="john@example.com")

            token = await forgot_password(body, mock_db)

        assert token is None
        mock_redis.set.assert_not_awaited()


class TestResetPassword:
    async def test_success(self, mock_db, mock_redis):
        user = _make_user()
        mock_redis.getdel.return_value = str(user.id)

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=user)
            mock_repo.update = AsyncMock(return_value=user)
            body = ResetPasswordRequest(token="reset-tok", new_password="newsecure123")

            await reset_password(body, mock_db)

        assert user.hashed_password != "$2b$12$fakehash"
        mock_redis.getdel.assert_awaited_once_with("reset:reset-tok")

    async def test_invalid_token_raises(self, mock_db, mock_redis):
        mock_redis.getdel.return_value = None

        with patch("app.services.auth_service.get_redis", return_value=mock_redis):
            body = ResetPasswordRequest(token="bad-tok", new_password="newsecure123")

            with pytest.raises(InvalidTokenError):
                await reset_password(body, mock_db)

    async def test_user_not_found_raises(self, mock_db, mock_redis):
        mock_redis.getdel.return_value = str(uuid.uuid4())

        with (
            patch("app.services.auth_service.get_redis", return_value=mock_redis),
            patch("app.services.auth_service.user_repository") as mock_repo,
        ):
            mock_repo.get_by_id = AsyncMock(return_value=None)
            body = ResetPasswordRequest(token="orphan-tok", new_password="newsecure123")

            with pytest.raises(InvalidTokenError):
                await reset_password(body, mock_db)
