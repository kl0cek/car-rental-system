import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.user_cache import (
    _serialize_user,
    cache_user_model,
    get_cached_user_model,
    invalidate_user_cache,
)
from app.models.user import User, UserRole


def _make_user(
    user_id: uuid.UUID | None = None,
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
) -> User:
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$secrethash",
        first_name="Test",
        last_name="User",
        role=role,
        is_active=is_active,
        is_verified=False,
        risk_score=Decimal("0.00"),
    )
    user.id = user_id or uuid.uuid4()
    return user


@pytest.fixture
def mock_redis():
    return AsyncMock()


class TestSerializeUser:
    def test_excludes_hashed_password(self):
        user = _make_user()
        data = _serialize_user(user)

        assert "hashed_password" not in data

    def test_includes_required_fields(self):
        user = _make_user()
        data = _serialize_user(user)

        assert data["email"] == "test@example.com"
        assert data["role"] == "customer"
        assert data["id"] == str(user.id)
        assert data["is_active"] is True


class TestGetCachedUserModel:
    @pytest.mark.asyncio
    async def test_returns_none_on_cache_miss(self, mock_redis):
        mock_redis.get.return_value = None
        user_id = uuid.uuid4()

        result = await get_cached_user_model(mock_redis, user_id)

        assert result is None
        mock_redis.get.assert_awaited_once_with(f"user:{user_id}")

    @pytest.mark.asyncio
    async def test_returns_user_on_cache_hit(self, mock_redis):
        user = _make_user()
        mock_redis.get.return_value = json.dumps(_serialize_user(user))

        result = await get_cached_user_model(mock_redis, user.id)

        assert result is not None
        assert result.email == "test@example.com"
        assert result.role == UserRole.CUSTOMER
        assert result.id == user.id
        assert result.hashed_password == ""

    @pytest.mark.asyncio
    async def test_returns_none_on_corrupt_json(self, mock_redis):
        mock_redis.get.return_value = "not-valid-json{{"
        user_id = uuid.uuid4()

        result = await get_cached_user_model(mock_redis, user_id)

        assert result is None
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_on_missing_fields(self, mock_redis):
        mock_redis.get.return_value = json.dumps({"email": "x@y.com"})
        user_id = uuid.uuid4()

        result = await get_cached_user_model(mock_redis, user_id)

        assert result is None


class TestCacheUserModel:
    @pytest.mark.asyncio
    async def test_stores_serialized_user_with_ttl(self, mock_redis):
        user = _make_user()

        await cache_user_model(mock_redis, user)

        mock_redis.set.assert_awaited_once()
        call_args = mock_redis.set.await_args
        assert call_args.args[0] == f"user:{user.id}"
        stored = json.loads(call_args.args[1])
        assert stored["email"] == "test@example.com"
        assert "hashed_password" not in stored
        assert call_args.kwargs["ex"] == 300


class TestInvalidateUserCache:
    @pytest.mark.asyncio
    async def test_deletes_cache_key(self, mock_redis):
        user_id = uuid.uuid4()

        await invalidate_user_cache(mock_redis, user_id)

        mock_redis.delete.assert_awaited_once_with(f"user:{user_id}")
