import asyncio
import secrets
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import EmailAlreadyRegisteredError
from app.core.user_cache import invalidate_user_cache
from app.db.redis import get_redis
from app.models.rental import Rental, Reservation
from app.models.user import User
from app.repositories import rental_repository, reservation_repository, user_repository
from app.schemas.user import (
    AdminReservationListParams,
    AdminUserListParams,
    UserProfileUpdate,
    UserRentalsListParams,
)

AVATAR_UPLOAD_DIR = Path("uploads/avatars")
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
IMAGE_FORMAT_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def update_user(db: AsyncSession, user: User) -> User:
    user = await user_repository.update(db, user)
    redis = get_redis()
    await invalidate_user_cache(redis, user.id)
    return user


async def update_profile(
    db: AsyncSession,
    current_user: User,
    body: UserProfileUpdate,
) -> tuple[User, str | None]:
    """Update profile. Returns (user, verification_token) — token is non-None
    only when the email was changed and a new verification email must be sent.
    """
    verification_token: str | None = None

    if body.email is not None and body.email != current_user.email:
        existing = await user_repository.get_by_email(db, body.email)
        if existing is not None and existing.id != current_user.id:
            raise EmailAlreadyRegisteredError(body.email)
        current_user.email = body.email
        current_user.is_verified = False

        verification_token = secrets.token_urlsafe(32)
        redis = get_redis()
        await redis.set(
            f"verify:{verification_token}",
            str(current_user.id),
            ex=settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 3600,
        )

    if body.first_name is not None:
        current_user.first_name = body.first_name
    if body.last_name is not None:
        current_user.last_name = body.last_name
    if body.phone is not None:
        current_user.phone = body.phone or None

    try:
        user = await update_user(db, current_user)
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyRegisteredError(body.email or current_user.email)

    return user, verification_token


def _validate_and_detect_image(contents: bytes) -> str:
    try:
        with Image.open(BytesIO(contents)) as img:
            img.verify()
            detected: str | None = img.format
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is not a valid image",
        )
    if detected is None or detected not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Avatar must be a JPEG, PNG or WEBP image",
        )
    return detected


async def upload_avatar(
    db: AsyncSession,
    current_user: User,
    file: UploadFile,
) -> User:
    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Avatar exceeds the 5 MB size limit",
        )

    detected_format = _validate_and_detect_image(contents)
    extension = IMAGE_FORMAT_EXTENSIONS[detected_format]

    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex}{extension}"
    destination = AVATAR_UPLOAD_DIR / filename
    await asyncio.to_thread(destination.write_bytes, contents)

    previous_url = current_user.avatar_url
    current_user.avatar_url = f"/static/avatars/{filename}"
    user = await update_user(db, current_user)

    if previous_url and previous_url.startswith("/static/avatars/"):
        previous_path = AVATAR_UPLOAD_DIR / previous_url.removeprefix("/static/avatars/")
        await asyncio.to_thread(_safe_unlink, previous_path)

    return user


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


async def list_user_rentals(
    db: AsyncSession,
    current_user: User,
    params: UserRentalsListParams,
) -> tuple[list[Rental], int]:
    return await rental_repository.get_list_by_user(
        db,
        current_user.id,
        offset=params.offset,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        date_from=params.date_from,
        date_to=params.date_to,
        status=params.status,
    )


async def list_admin_reservations(
    db: AsyncSession,
    params: AdminReservationListParams,
) -> tuple[list[Reservation], int]:
    return await reservation_repository.get_admin_list(
        db,
        offset=params.offset,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        status=params.status,
        user_id=params.user_id,
        vehicle_id=params.vehicle_id,
        date_from=params.date_from,
        date_to=params.date_to,
    )


async def list_admin_users(
    db: AsyncSession,
    params: AdminUserListParams,
) -> tuple[list[User], int]:
    return await user_repository.get_admin_list(
        db,
        offset=params.offset,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        role=params.role,
        is_active=params.is_active,
        is_verified=params.is_verified,
        min_risk_score=params.min_risk_score,
        max_risk_score=params.max_risk_score,
        active_since=params.active_since,
        search=params.search,
    )


