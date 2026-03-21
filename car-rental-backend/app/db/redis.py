from redis.asyncio import Redis

from app.config import settings

redis_client: Redis | None = None


def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not initialized. Call connect_redis() first.")
    return redis_client


async def connect_redis() -> None:
    global redis_client
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
