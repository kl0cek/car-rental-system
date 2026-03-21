from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user_cache import invalidate_user_cache
from app.db.redis import get_redis
from app.models.user import User
from app.repositories import user_repository


async def update_user(db: AsyncSession, user: User) -> User:
    user = await user_repository.update(db, user)
    redis = get_redis()
    await invalidate_user_cache(redis, user.id)
    return user
