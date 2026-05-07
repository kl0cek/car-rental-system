"""Router panelu admina dla pojazdów (`/admin/vehicles`).

CRUD pojazdów, zarządzanie galerią zdjęć (upload/usuwanie/reorder/primary)
oraz zbiorcza zmiana statusu floty. Wymaga roli ADMIN. Body multipart
jest parsowane ręcznie przez Pydantic, bo FastAPI nie zintegruje formularza
z zagnieżdżonymi typami w jednej funkcji.
"""

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi import status as http_status
from pydantic import ValidationError

from app.core.deps import require_roles
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.models.vehicle import EngineType, VehicleStatus
from app.schemas.vehicle import (
    VehicleBulkStatusResponse,
    VehicleBulkStatusUpdate,
    VehicleCreate,
    VehicleDetailResponse,
    VehicleUpdate,
)
from app.services import vehicle_service

router = APIRouter(prefix="/admin/vehicles", tags=["admin", "vehicles"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def _validation_error_to_http(exc: ValidationError) -> HTTPException:
    return HTTPException(
        status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()],
    )


@router.post(
    "",
    response_model=VehicleDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a new vehicle (admin only)",
)
async def create_vehicle(
    db: DbSession,
    _: AdminUser,
    brand: Annotated[str, Form()],
    model: Annotated[str, Form()],
    year: Annotated[int, Form()],
    license_plate: Annotated[str, Form()],
    vin: Annotated[str, Form()],
    engine_type: Annotated[EngineType, Form()],
    horsepower: Annotated[int, Form()],
    seats: Annotated[int, Form()],
    trunk_capacity: Annotated[int, Form()],
    daily_base_price: Annotated[Decimal, Form()],
    color: Annotated[str, Form()],
    category_id: Annotated[uuid.UUID, Form()],
    mileage: Annotated[int, Form()] = 0,
    status: Annotated[VehicleStatus, Form()] = VehicleStatus.AVAILABLE,
    images: Annotated[list[UploadFile] | None, File()] = None,
) -> VehicleDetailResponse:
    try:
        body = VehicleCreate(
            brand=brand,
            model=model,
            year=year,
            license_plate=license_plate,
            vin=vin,
            engine_type=engine_type,
            horsepower=horsepower,
            seats=seats,
            trunk_capacity=trunk_capacity,
            daily_base_price=daily_base_price,
            color=color,
            category_id=category_id,
            mileage=mileage,
            status=status,
        )
    except ValidationError as exc:
        raise _validation_error_to_http(exc)

    return await vehicle_service.create_vehicle(db, body, images)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleDetailResponse,
    summary="Update vehicle scalar fields (admin only). Images managed via dedicated endpoints.",
)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
    brand: Annotated[str | None, Form()] = None,
    model: Annotated[str | None, Form()] = None,
    year: Annotated[int | None, Form()] = None,
    license_plate: Annotated[str | None, Form()] = None,
    vin: Annotated[str | None, Form()] = None,
    engine_type: Annotated[EngineType | None, Form()] = None,
    horsepower: Annotated[int | None, Form()] = None,
    seats: Annotated[int | None, Form()] = None,
    trunk_capacity: Annotated[int | None, Form()] = None,
    daily_base_price: Annotated[Decimal | None, Form()] = None,
    color: Annotated[str | None, Form()] = None,
    category_id: Annotated[uuid.UUID | None, Form()] = None,
    mileage: Annotated[int | None, Form()] = None,
    status: Annotated[VehicleStatus | None, Form()] = None,
) -> VehicleDetailResponse:
    raw_fields = {
        "brand": brand,
        "model": model,
        "year": year,
        "license_plate": license_plate,
        "vin": vin,
        "engine_type": engine_type,
        "horsepower": horsepower,
        "seats": seats,
        "trunk_capacity": trunk_capacity,
        "daily_base_price": daily_base_price,
        "color": color,
        "category_id": category_id,
        "mileage": mileage,
        "status": status,
    }
    provided = {k: v for k, v in raw_fields.items() if v is not None}

    try:
        body = VehicleUpdate(**provided)
    except ValidationError as exc:
        raise _validation_error_to_http(exc)

    result = await vehicle_service.update_vehicle(db, vehicle_id, body)
    if result is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return result


@router.delete(
    "/{vehicle_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a vehicle (admin only)",
)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
) -> Response:
    found = await vehicle_service.delete_vehicle(db, vehicle_id)
    if not found:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.patch(
    "/bulk-status",
    response_model=VehicleBulkStatusResponse,
    summary="Bulk-update status across many vehicles (admin only)",
)
async def bulk_update_status(
    body: VehicleBulkStatusUpdate,
    db: DbSession,
    _: AdminUser,
) -> VehicleBulkStatusResponse:
    return await vehicle_service.bulk_update_status(db, body.ids, body.status)


@router.post(
    "/{vehicle_id}/images",
    response_model=VehicleDetailResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Upload an additional image for a vehicle (admin only)",
)
async def upload_vehicle_image(
    vehicle_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
    image: Annotated[UploadFile, File()],
    is_primary: Annotated[bool, Form()] = False,
) -> VehicleDetailResponse:
    result = await vehicle_service.add_vehicle_image(db, vehicle_id, image, is_primary)
    if result is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return result


@router.delete(
    "/{vehicle_id}/images/{image_id}",
    response_model=VehicleDetailResponse,
    summary="Delete a vehicle image (admin only)",
)
async def delete_vehicle_image(
    vehicle_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
) -> VehicleDetailResponse:
    result = await vehicle_service.delete_vehicle_image(db, vehicle_id, image_id)
    if result is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return result


@router.post(
    "/{vehicle_id}/images/{image_id}/primary",
    response_model=VehicleDetailResponse,
    summary="Mark a vehicle image as the primary one (admin only)",
)
async def set_vehicle_primary_image(
    vehicle_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
) -> VehicleDetailResponse:
    result = await vehicle_service.set_vehicle_primary_image(db, vehicle_id, image_id)
    if result is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return result


@router.put(
    "/{vehicle_id}/images/order",
    response_model=VehicleDetailResponse,
    summary="Reorder vehicle images (admin only)",
)
async def reorder_vehicle_images(
    vehicle_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
    ordered_ids: list[uuid.UUID],
) -> VehicleDetailResponse:
    result = await vehicle_service.reorder_vehicle_images(db, vehicle_id, ordered_ids)
    if result is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return result
