import secrets
import uuid
from asyncio import get_running_loop
from datetime import UTC, datetime, timedelta

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
from app.core.user_cache import invalidate_user_cache
from app.db.redis import get_redis
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
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


async def login_user(body: LoginRequest, db: AsyncSession) -> tuple[TokenResponse, User]:
    user = await user_repository.get_by_email(db, body.email)
    if user is None:
        raise InvalidCredentialsError("User not found")

    if not user.is_active:
        raise InvalidCredentialsError("Account is disabled")

    if not user.is_verified:
        raise InvalidCredentialsError("Email address is not verified")

    loop = get_running_loop()
    is_valid = await loop.run_in_executor(
        None, verify_password, body.password, user.hashed_password
    )
    if not is_valid:
        raise InvalidCredentialsError("Wrong password")

    access_token = create_access_token(subject=str(user.id), role=user.role)
    refresh_token = create_refresh_token(subject=str(user.id), role=user.role)

    await user_repository.update_last_login(db, user, datetime.now(tz=UTC))
    await invalidate_user_cache(get_redis(), user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token), user


async def refresh_tokens(body: RefreshRequest, db: AsyncSession) -> tuple[TokenResponse, User]:
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise InvalidTokenError("Token is not a refresh token")

    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise InvalidTokenError("Missing subject in token")

    redis = get_redis()

    if await is_token_blacklisted(redis, body.refresh_token):
        raise InvalidTokenError("Refresh token has been revoked")

    refresh_ttl = int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    await blacklist_token(redis, body.refresh_token, refresh_ttl)

    user = await user_repository.get_by_id(db, uuid.UUID(sub))
    if user is None or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    access_token = create_access_token(subject=sub, role=user.role)
    new_refresh_token = create_refresh_token(subject=sub, role=user.role)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token), user


async def logout_user_tokens(access_token: str | None, refresh_token: str | None) -> None:
    redis = get_redis()

    if refresh_token:
        refresh_ttl = int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
        await blacklist_token(redis, refresh_token, refresh_ttl)

    if access_token:
        access_ttl = int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
        await blacklist_token(redis, access_token, access_ttl)


async def verify_email(token: str, db: AsyncSession) -> None:
    redis = get_redis()
    user_id_raw = await redis.getdel(f"verify:{token}")
    if user_id_raw is None:
        raise InvalidTokenError("Verification token not found or expired")

    user = await user_repository.get_by_id(db, uuid.UUID(user_id_raw))
    if user is None:
        raise InvalidTokenError("User associated with verification token not found")

    if user.is_verified:
        return

    user.is_verified = True
    await user_repository.update(db, user)


async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession) -> str | None:
    """Returns reset token if user exists, None otherwise.

    Always returns silently to prevent email enumeration.
    Enforces a 60-second per-user cooldown to prevent spam.
    """
    user = await user_repository.get_by_email(db, body.email)
    if user is None:
        return None

    redis = get_redis()
    cooldown_key = f"reset_cooldown:{user.id}"
    if await redis.exists(cooldown_key):
        return None

    token = secrets.token_urlsafe(32)
    ttl = settings.RESET_PASSWORD_TOKEN_EXPIRE_HOURS * 3600
    await redis.set(f"reset:{token}", str(user.id), ex=ttl)
    await redis.set(cooldown_key, "1", ex=60)
    return token


async def reset_password(body: ResetPasswordRequest, db: AsyncSession) -> None:
    redis = get_redis()
    user_id_raw = await redis.getdel(f"reset:{body.token}")
    if user_id_raw is None:
        raise InvalidTokenError("Reset token not found or expired")

    user = await user_repository.get_by_id(db, uuid.UUID(user_id_raw))
    if user is None:
        raise InvalidTokenError("User associated with reset token not found")

    loop = get_running_loop()
    hashed = await loop.run_in_executor(None, hash_password, body.new_password)

    user.hashed_password = hashed
    await user_repository.update(db, user)
