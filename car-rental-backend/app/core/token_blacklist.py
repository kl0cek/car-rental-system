import hashlib

from redis.asyncio import Redis


def _token_key(raw_token: str) -> str:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return f"blacklist:{token_hash}"


async def blacklist_token(redis: Redis, raw_token: str, ttl: int) -> None:
    await redis.set(_token_key(raw_token), "1", ex=ttl)


async def is_token_blacklisted(redis: Redis, raw_token: str) -> bool:
    return bool(await redis.exists(_token_key(raw_token)))
