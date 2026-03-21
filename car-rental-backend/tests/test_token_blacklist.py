import hashlib
from unittest.mock import AsyncMock

import pytest

from app.core.token_blacklist import blacklist_token, is_token_blacklisted


@pytest.fixture
def mock_redis():
    return AsyncMock()


class TestBlacklistToken:
    @pytest.mark.asyncio
    async def test_blacklist_token_sets_key_with_ttl(self, mock_redis):
        await blacklist_token(mock_redis, "my-token", 3600)

        expected_key = f"blacklist:{hashlib.sha256(b'my-token').hexdigest()}"
        mock_redis.set.assert_awaited_once_with(expected_key, "1", ex=3600)

    @pytest.mark.asyncio
    async def test_blacklist_token_different_tokens_produce_different_keys(self, mock_redis):
        await blacklist_token(mock_redis, "token-a", 100)
        await blacklist_token(mock_redis, "token-b", 200)

        keys = [call.args[0] for call in mock_redis.set.await_args_list]
        assert keys[0] != keys[1]


class TestIsTokenBlacklisted:
    @pytest.mark.asyncio
    async def test_returns_true_when_token_exists(self, mock_redis):
        mock_redis.exists.return_value = 1

        result = await is_token_blacklisted(mock_redis, "revoked-token")

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_token_not_exists(self, mock_redis):
        mock_redis.exists.return_value = 0

        result = await is_token_blacklisted(mock_redis, "valid-token")

        assert result is False

    @pytest.mark.asyncio
    async def test_checks_correct_key(self, mock_redis):
        mock_redis.exists.return_value = 0

        await is_token_blacklisted(mock_redis, "check-me")

        expected_key = f"blacklist:{hashlib.sha256(b'check-me').hexdigest()}"
        mock_redis.exists.assert_awaited_once_with(expected_key)
