import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal

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
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "risk_score": str(user.risk_score),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _deserialize_user(data: dict[str, object]) -> User:
    last_login_raw = data.get("last_login_at")
    created_at_raw = data.get("created_at")
    updated_at_raw = data.get("updated_at")
    user = User(
        email=str(data["email"]),
        hashed_password="",
        first_name=str(data["first_name"]),
        last_name=str(data["last_name"]),
        role=UserRole(str(data["role"])),
        is_active=bool(data["is_active"]),
        is_verified=bool(data["is_verified"]),
        phone=str(data["phone"]) if data.get("phone") else None,
        avatar_url=str(data["avatar_url"]) if data.get("avatar_url") else None,
        risk_score=Decimal(str(data.get("risk_score", "0.00"))),
        last_login_at=datetime.fromisoformat(str(last_login_raw)) if last_login_raw else None,
    )
    user.id = uuid.UUID(str(data["id"]))
    if created_at_raw:
        user.created_at = datetime.fromisoformat(str(created_at_raw))
    if updated_at_raw:
        user.updated_at = datetime.fromisoformat(str(updated_at_raw))
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
