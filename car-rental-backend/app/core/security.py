from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import InvalidTokenError
from app.models.user import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    result: str = pwd_context.hash(password)
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def _create_token(
    subject: str, token_type: str, expires_delta: timedelta, extra: dict[str, object] | None = None
) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, object] = {"sub": subject, "exp": expire, "type": token_type}
    if extra:
        payload.update(extra)
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def create_access_token(subject: str, role: UserRole) -> str:
    return _create_token(
        subject, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        {"role": role.value},
    )


def create_refresh_token(subject: str, role: UserRole) -> str:
    return _create_token(
        subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        {"role": role.value},
    )


def decode_token(token: str) -> dict[str, object]:
    try:
        payload: dict[str, object] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise InvalidTokenError from e
