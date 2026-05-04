"""Serwis pojazdów — logika katalogu i panelu admina.

Listing z filtrowaniem (kategoria, dostępność, zakres dat), wyliczanie
ceny dziennej z mnożnikiem kategorii, CRUD dla admina, obsługa
zdjęć pojazdu (Pillow + post-commit unlink) oraz logowanie zmian
do MongoDB jako audyt.
"""

import asyncio
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.mongodb import get_mongo_db
from app.db.session import schedule_post_commit
from app.models.category import Category
from app.models.vehicle import Vehicle
from app.repositories import vehicle_repository
from app.schemas.vehicle import (
    AvailabilityRequest,
    AvailabilityResponse,
    PaginatedVehicleResponse,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleListItem,
    VehicleListParams,
    VehicleUpdate,
)

VEHICLE_IMAGE_UPLOAD_DIR = Path("uploads/vehicles")
ALLOWED_VEHICLE_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
VEHICLE_IMAGE_FORMAT_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
MAX_VEHICLE_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
VEHICLE_IMAGE_READ_CHUNK_BYTES = 64 * 1024
VEHICLE_IMAGE_PUBLIC_PREFIX = "/static/vehicles/"


async def list_vehicles(
    params: VehicleListParams,
    db: AsyncSession,
) -> PaginatedVehicleResponse:
    vehicles, total = await vehicle_repository.get_list(
        db,
        offset=params.offset,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        category=params.category,
        engine_type=params.engine_type,
        min_price=params.min_price,
        max_price=params.max_price,
        min_year=params.min_year,
        max_year=params.max_year,
        min_seats=params.min_seats,
        status=params.status,
        available_from=params.available_from,
        available_to=params.available_to,
    )

    return PaginatedVehicleResponse(
        items=[VehicleListItem.model_validate(v) for v in vehicles],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


async def get_vehicle_detail(
    vehicle_id: uuid.UUID,
    db: AsyncSession,
) -> VehicleDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None
    return await _build_detail_response(db, vehicle)


async def check_availability(
    vehicle_id: uuid.UUID,
    body: AvailabilityRequest,
    db: AsyncSession,
) -> AvailabilityResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    conflicts = await vehicle_repository.count_conflicting_reservations(
        db, vehicle_id, body.start_date, body.end_date
    )

    return AvailabilityResponse(
        vehicle_id=vehicle_id,
        available=conflicts == 0,
        start_date=body.start_date,
        end_date=body.end_date,
        conflicting_rentals=conflicts,
    )


def _validate_and_detect_image(contents: bytes) -> str:
    # Pillow.verify() faktycznie sprawdza nagłówki obrazu —
    # nie polegamy na rozszerzeniu pliku ani na content-type od klienta
    try:
        with Image.open(BytesIO(contents)) as img:
            img.verify()
            detected: str | None = img.format
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is not a valid image",
        )
    if detected is None or detected not in ALLOWED_VEHICLE_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vehicle image must be a JPEG, PNG or WEBP image",
        )
    return detected


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


async def _read_upload_capped(file: UploadFile, max_bytes: int) -> bytes:
    """Read at most ``max_bytes`` from ``file`` in chunks; raise 413 if exceeded.

    ``UploadFile.read()`` with no argument loads the whole body into a single
    bytes object, so a malicious client could exhaust memory before any size
    check fires. Read in chunks and abort as soon as the cap is breached.
    """
    buf = bytearray()
    while True:
        chunk = await file.read(VEHICLE_IMAGE_READ_CHUNK_BYTES)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Vehicle image exceeds the 5 MB size limit",
            )
    return bytes(buf)


async def _persist_vehicle_image(file: UploadFile, vehicle_id: uuid.UUID) -> str:
    """Validate image, write to disk, return public URL."""
    contents = await _read_upload_capped(file, MAX_VEHICLE_IMAGE_SIZE_BYTES)

    detected_format = _validate_and_detect_image(contents)
    extension = VEHICLE_IMAGE_FORMAT_EXTENSIONS[detected_format]

    VEHICLE_IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{vehicle_id}_{uuid.uuid4().hex}{extension}"
    destination = VEHICLE_IMAGE_UPLOAD_DIR / filename
    await asyncio.to_thread(destination.write_bytes, contents)

    return f"{VEHICLE_IMAGE_PUBLIC_PREFIX}{filename}"


def _local_image_path(image_url: str | None) -> Path | None:
    if not image_url or not image_url.startswith(VEHICLE_IMAGE_PUBLIC_PREFIX):
        return None
    relative = image_url.removeprefix(VEHICLE_IMAGE_PUBLIC_PREFIX)
    return VEHICLE_IMAGE_UPLOAD_DIR / relative


async def _unlink_image_now(image_url: str | None) -> None:
    """Unlink immediately. Use only after a rollback — never while a transaction is open."""
    path = _local_image_path(image_url)
    if path is not None:
        await asyncio.to_thread(_safe_unlink, path)


def _schedule_image_unlink(db: AsyncSession, image_url: str | None) -> None:
    """Defer unlink until the request transaction commits successfully."""
    path = _local_image_path(image_url)
    if path is None:
        return

    async def _hook() -> None:
        await asyncio.to_thread(_safe_unlink, path)

    schedule_post_commit(db, _hook)


async def _ensure_category_exists(db: AsyncSession, category_id: uuid.UUID) -> None:
    result = await db.execute(select(Category.id).where(Category.id == category_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid category_id: category does not exist",
        )


def _integrity_error_to_http(exc: IntegrityError) -> HTTPException:
    msg = str(getattr(exc, "orig", exc)).lower()
    if "vin" in msg:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vehicle with this VIN already exists",
        )
    if "license_plate" in msg or "license plate" in msg:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vehicle with this license plate already exists",
        )
    if "category" in msg or "foreign key" in msg:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid category_id: category does not exist",
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Vehicle violates a uniqueness or referential constraint",
    )


async def _build_detail_response(db: AsyncSession, vehicle: Vehicle) -> VehicleDetailResponse:
    booked_dates = await vehicle_repository.get_booked_dates(db, vehicle.id)
    average_rating, review_count = await _get_review_stats(vehicle.id)
    return VehicleDetailResponse(
        id=vehicle.id,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        engine_type=vehicle.engine_type,
        horsepower=vehicle.horsepower,
        seats=vehicle.seats,
        trunk_capacity=vehicle.trunk_capacity,
        daily_base_price=vehicle.daily_base_price,
        color=vehicle.color,
        mileage=vehicle.mileage,
        image_url=vehicle.image_url,
        status=vehicle.status,
        is_active=vehicle.is_active,
        category=vehicle.category,
        average_rating=average_rating,
        review_count=review_count,
        booked_dates=booked_dates,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


async def create_vehicle(
    db: AsyncSession,
    body: VehicleCreate,
    image: UploadFile | None,
) -> VehicleDetailResponse:
    await _ensure_category_exists(db, body.category_id)

    vehicle = Vehicle(
        brand=body.brand,
        model=body.model,
        year=body.year,
        license_plate=body.license_plate,
        vin=body.vin,
        engine_type=body.engine_type,
        horsepower=body.horsepower,
        seats=body.seats,
        trunk_capacity=body.trunk_capacity,
        daily_base_price=body.daily_base_price,
        color=body.color,
        mileage=body.mileage,
        status=body.status,
        category_id=body.category_id,
        is_active=True,
    )

    image_url: str | None = None
    if image is not None and image.filename:
        # Generujemy ID z góry — bez tego nazwa pliku byłaby znana dopiero
        # po flush, co zmusiłoby do dwóch zapisów do bazy
        if vehicle.id is None:
            vehicle.id = uuid.uuid4()
        image_url = await _persist_vehicle_image(image, vehicle.id)
        vehicle.image_url = image_url

    try:
        vehicle = await vehicle_repository.create(db, vehicle)
    except IntegrityError as exc:
        await db.rollback()
        # Clean up the orphan file we wrote — rollback already happened, so unlink now.
        if image_url is not None:
            await _unlink_image_now(image_url)
        raise _integrity_error_to_http(exc)

    # Eager-load category for response
    stmt = select(Vehicle).options(joinedload(Vehicle.category)).where(Vehicle.id == vehicle.id)
    vehicle = (await db.execute(stmt)).scalar_one()
    return await _build_detail_response(db, vehicle)


async def update_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
    image: UploadFile | None,
) -> VehicleDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    if body.category_id is not None and body.category_id != vehicle.category_id:
        await _ensure_category_exists(db, body.category_id)

    # Apply scalar field updates
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    previous_image_url = vehicle.image_url
    new_image_url: str | None = None
    if image is not None and image.filename:
        new_image_url = await _persist_vehicle_image(image, vehicle.id)
        vehicle.image_url = new_image_url

    try:
        vehicle = await vehicle_repository.update(db, vehicle)
    except IntegrityError as exc:
        await db.rollback()
        if new_image_url is not None:
            await _unlink_image_now(new_image_url)
        raise _integrity_error_to_http(exc)

    # If the image was successfully replaced, defer unlinking the previous file
    # until after the request transaction commits — otherwise a later error in
    # this request would roll back the DB but leave the filesystem changed.
    if new_image_url is not None and previous_image_url != new_image_url:
        _schedule_image_unlink(db, previous_image_url)

    # Re-fetch with category eager-loaded for response
    stmt = select(Vehicle).options(joinedload(Vehicle.category)).where(Vehicle.id == vehicle.id)
    vehicle = (await db.execute(stmt)).scalar_one()
    return await _build_detail_response(db, vehicle)


async def delete_vehicle(db: AsyncSession, vehicle_id: uuid.UUID) -> bool:
    """Soft-delete a vehicle. Returns False if not found, raises 409 if blocked."""
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return False

    if await vehicle_repository.has_blocking_reservations(db, vehicle_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete vehicle with active, pending, or confirmed reservations",
        )

    await vehicle_repository.soft_delete(db, vehicle)
    return True


async def _get_review_stats(vehicle_id: uuid.UUID) -> tuple[float | None, int]:
    mongo_db = get_mongo_db()
    pipeline: list[dict[str, Any]] = [
        {"$match": {"vehicle_id": str(vehicle_id)}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    results = await mongo_db.reviews.aggregate(pipeline).to_list(1)
    if not results:
        return None, 0
    doc = results[0]
    return round(doc["avg"], 2), doc["count"]
