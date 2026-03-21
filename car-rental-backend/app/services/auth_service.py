import secrets
from asyncio import get_running_loop

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.redis import get_redis
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register_user(body: RegisterRequest, db: AsyncSession) -> tuple[User, str]:
    existing = await user_repository.get_by_email(db, body.email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(body.email)

    loop = get_running_loop()
    hashed = await loop.run_in_executor(None, hash_password, body.password)

    user = User(
        email=body.email,
        hashed_password=hashed,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )
    user = await user_repository.create(db, user)

    token = secrets.token_urlsafe(32)
    redis = get_redis()
    await redis.set(
        f"verify:{token}",
        str(user.id),
        ex=settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 3600,
    )

    return user, token


async def login_user(body: LoginRequest, db: AsyncSession) -> TokenResponse:
    user = await user_repository.get_by_email(db, body.email)
    if user is None:
        raise InvalidCredentialsError

    loop = get_running_loop()
    is_valid = await loop.run_in_executor(
        None, verify_password, body.password, user.hashed_password
    )
    if not is_valid:
        raise InvalidCredentialsError

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
