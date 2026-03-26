import json
import logging
import uuid

from redis.asyncio import Redis

from app.config import settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

_KEY_PREFIX = "user:"


def _cache_key(user_id: uuid.UUID) -> str:
    return f"{_KEY_PREFIX}{user_id}"


def _serialize_user(user: User) -> dict[str, object]:
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone": user.phone,
    }


def _deserialize_user(data: dict[str, object]) -> User:
    user = User(
        email=str(data["email"]),
        hashed_password="",
        first_name=str(data["first_name"]),
        last_name=str(data["last_name"]),
        role=UserRole(str(data["role"])),
        is_active=bool(data["is_active"]),
        is_verified=bool(data["is_verified"]),
        phone=str(data["phone"]) if data.get("phone") else None,
    )
    user.id = uuid.UUID(str(data["id"]))
    return user


async def get_cached_user_model(redis: Redis, user_id: uuid.UUID) -> User | None:
    raw = await redis.get(_cache_key(user_id))
    if raw is None:
        return None
    try:
        data: dict[str, object] = json.loads(raw)
        return _deserialize_user(data)
    except Exception:
        logger.warning("Corrupt user cache for %s, falling through to DB", user_id)
        await redis.delete(_cache_key(user_id))
        return None


async def cache_user_model(redis: Redis, user: User) -> None:
    await redis.set(
        _cache_key(user.id),
        json.dumps(_serialize_user(user)),
        ex=settings.USER_CACHE_TTL_SECONDS,
    )


async def invalidate_user_cache(redis: Redis, user_id: uuid.UUID) -> None:
    await redis.delete(_cache_key(user_id))
