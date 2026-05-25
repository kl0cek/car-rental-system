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
from sqlalchemy.orm import joinedload, selectinload

from app.db.session import schedule_post_commit
from app.models.category import Category
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.vehicle_image import VehicleImage
from app.repositories import vehicle_repository
from app.schemas.vehicle import (
    AvailabilityRequest,
    AvailabilityResponse,
    PaginatedVehicleResponse,
    VehicleAdminDetailResponse,
    VehicleBulkStatusResponse,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleImageResponse,
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


def _primary_image_url(images: list[VehicleImage]) -> str | None:
    for img in images:
        if img.is_primary:
            return img.url
    # Defensive fallback — vehicles without a primary flag still want a thumbnail
    if images:
        return min(images, key=lambda i: i.position).url
    return None


def _serialize_images(images: list[VehicleImage]) -> list[VehicleImageResponse]:
    ordered = sorted(images, key=lambda i: i.position)
    return [VehicleImageResponse.model_validate(img) for img in ordered]


def _build_list_item(vehicle: Vehicle) -> VehicleListItem:
    return VehicleListItem(
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
        image_url=_primary_image_url(vehicle.images),
        images=_serialize_images(vehicle.images),
        status=vehicle.status,
        category=vehicle.category,
    )


PUBLIC_CATALOG_STATUSES: list[VehicleStatus] = [
    VehicleStatus.AVAILABLE,
    VehicleStatus.RENTED,
]


async def list_vehicles(
    params: VehicleListParams,
    db: AsyncSession,
) -> PaginatedVehicleResponse:
    # Public catalog must never surface MAINTENANCE / OUT_OF_SERVICE vehicles —
    # whitelist the visible statuses here so the router doesn't have to know
    # the policy. ``params.status`` is no longer set by the public router but
    # is still honoured if set (future admin caller could reuse this service).
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
        status_in=PUBLIC_CATALOG_STATUSES,
        available_from=params.available_from,
        available_to=params.available_to,
        search=params.search,
    )

    return PaginatedVehicleResponse(
        items=[_build_list_item(v) for v in vehicles],
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


async def get_vehicle_admin_detail(
    vehicle_id: uuid.UUID,
    db: AsyncSession,
) -> VehicleAdminDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None
    return await _build_admin_detail_response(db, vehicle)


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


# Map of asyncpg constraint names -> response. Source of truth: ``Vehicle``
# table definition + Alembic migrations.
_VEHICLE_CONSTRAINT_RESPONSES: dict[str, tuple[int, str]] = {
    "uq_vehicles_vin_active": (
        status.HTTP_409_CONFLICT,
        "A vehicle with this VIN already exists",
    ),
    "uq_vehicles_license_plate_active": (
        status.HTTP_409_CONFLICT,
        "A vehicle with this license plate already exists",
    ),
    "fk_vehicles_category_id": (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Invalid category_id: category does not exist",
    ),
}


def _integrity_error_to_http(exc: IntegrityError) -> HTTPException:
    """Translate a DB integrity violation into the right HTTP error.

    Prefer the asyncpg constraint name (which is stable) over substring
    matching against the rendered SQL message (which can change between
    PostgreSQL versions or locales). Fall back to substring matching so the
    handler still does something sensible against other DB drivers or when
    asyncpg's diag isn't populated.
    """
    orig = getattr(exc, "orig", None)

    # asyncpg surfaces the original UniqueViolationError/ForeignKeyViolationError
    # as the chained ``__cause__`` of the DBAPI wrapper; older versions store
    # it directly on ``orig``. Walk both.
    constraint_name: str | None = None
    for candidate in (orig, getattr(orig, "__cause__", None)):
        if candidate is None:
            continue
        # asyncpg PostgresError exposes constraint_name directly
        name = getattr(candidate, "constraint_name", None)
        if isinstance(name, str) and name:
            constraint_name = name
            break
        # Some drivers expose it under .diag.constraint_name
        diag = getattr(candidate, "diag", None)
        diag_name = getattr(diag, "constraint_name", None) if diag is not None else None
        if isinstance(diag_name, str) and diag_name:
            constraint_name = diag_name
            break

    if constraint_name is not None:
        mapped = _VEHICLE_CONSTRAINT_RESPONSES.get(constraint_name)
        if mapped is not None:
            status_code, detail = mapped
            return HTTPException(status_code=status_code, detail=detail)

    # Resilience fallback: substring match. Useful for non-asyncpg drivers
    # (e.g. sqlite in tests) where constraint_name may be unavailable.
    msg = str(orig if orig is not None else exc).lower()
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


async def _detail_payload(db: AsyncSession, vehicle: Vehicle) -> dict[str, Any]:
    """Shared field bag for both public and admin detail responses."""
    booked_dates = await vehicle_repository.get_booked_dates(db, vehicle.id)
    # avg_rating / ratings_count are persisted on the vehicle row by
    # review_service after each review insert/delete — read them directly
    # instead of aggregating from Mongo on every detail request.
    average_rating = float(vehicle.avg_rating) if vehicle.avg_rating is not None else None
    return {
        "id": vehicle.id,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "engine_type": vehicle.engine_type,
        "horsepower": vehicle.horsepower,
        "seats": vehicle.seats,
        "trunk_capacity": vehicle.trunk_capacity,
        "daily_base_price": vehicle.daily_base_price,
        "color": vehicle.color,
        "mileage": vehicle.mileage,
        "image_url": _primary_image_url(vehicle.images),
        "images": _serialize_images(vehicle.images),
        "status": vehicle.status,
        "is_active": vehicle.is_active,
        "category": vehicle.category,
        "average_rating": average_rating,
        "review_count": vehicle.ratings_count,
        "booked_dates": booked_dates,
        "created_at": vehicle.created_at,
        "updated_at": vehicle.updated_at,
    }


async def _build_detail_response(db: AsyncSession, vehicle: Vehicle) -> VehicleDetailResponse:
    # Public response — VIN and license plate intentionally excluded.
    return VehicleDetailResponse.model_validate(await _detail_payload(db, vehicle))


async def _build_admin_detail_response(
    db: AsyncSession, vehicle: Vehicle
) -> VehicleAdminDetailResponse:
    payload = await _detail_payload(db, vehicle)
    payload["license_plate"] = vehicle.license_plate
    payload["vin"] = vehicle.vin
    return VehicleAdminDetailResponse.model_validate(payload)


async def create_vehicle(
    db: AsyncSession,
    body: VehicleCreate,
    images: list[UploadFile] | None,
) -> VehicleAdminDetailResponse:
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

    # Reserve the id up front so image filenames can be computed before the row
    # exists — keeps everything in one transaction.
    if vehicle.id is None:
        vehicle.id = uuid.uuid4()

    persisted_urls: list[str] = []
    files = [f for f in (images or []) if f is not None and f.filename]
    try:
        for upload in files:
            url = await _persist_vehicle_image(upload, vehicle.id)
            persisted_urls.append(url)
    except Exception:
        # Validation/size failure on file N: clean up files 0..N-1 we already wrote
        for url in persisted_urls:
            await _unlink_image_now(url)
        raise

    try:
        vehicle = await vehicle_repository.create(db, vehicle)

        for index, url in enumerate(persisted_urls):
            await vehicle_repository.add_image(db, vehicle.id, url, is_primary=(index == 0))
    except IntegrityError as exc:
        await db.rollback()
        for url in persisted_urls:
            await _unlink_image_now(url)
        raise _integrity_error_to_http(exc)

    stmt = (
        select(Vehicle)
        .options(joinedload(Vehicle.category), selectinload(Vehicle.images))
        .where(Vehicle.id == vehicle.id)
    )
    vehicle = (await db.execute(stmt)).scalar_one()
    return await _build_admin_detail_response(db, vehicle)


async def update_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    body: VehicleUpdate,
) -> VehicleAdminDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    if body.category_id is not None and body.category_id != vehicle.category_id:
        await _ensure_category_exists(db, body.category_id)

    # Apply scalar field updates
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    try:
        vehicle = await vehicle_repository.update(db, vehicle)
    except IntegrityError as exc:
        await db.rollback()
        raise _integrity_error_to_http(exc)

    stmt = (
        select(Vehicle)
        .options(joinedload(Vehicle.category), selectinload(Vehicle.images))
        .where(Vehicle.id == vehicle.id)
    )
    vehicle = (await db.execute(stmt)).scalar_one()
    return await _build_admin_detail_response(db, vehicle)


async def add_vehicle_image(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    image: UploadFile,
    is_primary: bool,
) -> VehicleAdminDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    url = await _persist_vehicle_image(image, vehicle_id)
    try:
        await vehicle_repository.add_image(db, vehicle_id, url, is_primary=is_primary)
    except IntegrityError as exc:
        await db.rollback()
        await _unlink_image_now(url)
        raise _integrity_error_to_http(exc)

    return await get_vehicle_admin_detail(vehicle_id, db)


async def delete_vehicle_image(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    image_id: uuid.UUID,
) -> VehicleAdminDetailResponse | None:
    image = await vehicle_repository.get_image(db, image_id)
    if image is None or image.vehicle_id != vehicle_id:
        return None

    url = image.url
    await vehicle_repository.delete_image(db, image)
    _schedule_image_unlink(db, url)
    return await get_vehicle_admin_detail(vehicle_id, db)


async def set_vehicle_primary_image(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    image_id: uuid.UUID,
) -> VehicleAdminDetailResponse | None:
    image = await vehicle_repository.get_image(db, image_id)
    if image is None or image.vehicle_id != vehicle_id:
        return None

    await vehicle_repository.set_primary_image(db, image)
    return await get_vehicle_admin_detail(vehicle_id, db)


async def reorder_vehicle_images(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    ordered_ids: list[uuid.UUID],
) -> VehicleAdminDetailResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    valid_ids = {img.id for img in vehicle.images}
    for img_id in ordered_ids:
        if img_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Image {img_id} does not belong to vehicle {vehicle_id}",
            )
    await vehicle_repository.reorder_images(db, vehicle_id, ordered_ids)
    return await get_vehicle_admin_detail(vehicle_id, db)


async def bulk_update_status(
    db: AsyncSession,
    ids: list[uuid.UUID],
    new_status: VehicleStatus,
) -> VehicleBulkStatusResponse:
    updated, missing = await vehicle_repository.bulk_update_status(db, ids, new_status)
    return VehicleBulkStatusResponse(updated=updated, not_found=missing)


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
