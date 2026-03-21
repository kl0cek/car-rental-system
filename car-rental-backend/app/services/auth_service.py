import secrets
import uuid
from asyncio import get_running_loop
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.token_blacklist import blacklist_token, is_token_blacklisted
from app.db.redis import get_redis
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)


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

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(body: RefreshRequest, db: AsyncSession) -> TokenResponse:
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise InvalidTokenError

    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise InvalidTokenError

    redis = get_redis()

    if await is_token_blacklisted(redis, body.refresh_token):
        raise InvalidTokenError

    refresh_ttl = int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    await blacklist_token(redis, body.refresh_token, refresh_ttl)

    user = await user_repository.get_by_id(db, uuid.UUID(sub))
    if user is None or not user.is_active:
        raise InvalidTokenError

    access_token = create_access_token(subject=sub, role=user.role)
    new_refresh_token = create_refresh_token(subject=sub, role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


async def logout_user(body: LogoutRequest) -> None:
    redis = get_redis()

    refresh_ttl = int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    await blacklist_token(redis, body.refresh_token, refresh_ttl)

    access_ttl = int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
    await blacklist_token(redis, body.access_token, access_ttl)
