import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status

from app.db.session import DbSession
from app.models.category import CategoryName
from app.models.vehicle import EngineType, VehicleStatus
from app.schemas.vehicle import (
    AvailabilityRequest,
    AvailabilityResponse,
    PaginatedVehicleResponse,
    SortableField,
    VehicleDetailResponse,
    VehicleListParams,
)
from app.services import vehicle_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=PaginatedVehicleResponse)
async def list_vehicles(
    db: DbSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: SortableField = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    category: CategoryName | None = Query(default=None),
    engine_type: EngineType | None = Query(default=None),
    min_price: Decimal | None = Query(default=None, ge=0, le=99999999),
    max_price: Decimal | None = Query(default=None, ge=0, le=99999999),
    min_year: int | None = Query(default=None, ge=1900),
    max_year: int | None = Query(default=None, le=2100),
    min_seats: int | None = Query(default=None, ge=1),
    status: VehicleStatus | None = Query(default=None),
    available_from: date | None = Query(default=None),
    available_to: date | None = Query(default=None),
) -> PaginatedVehicleResponse:
    if available_from and available_to and available_from > available_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="available_from must be before available_to",
        )
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )

    params = VehicleListParams(
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        category=category,
        engine_type=engine_type,
        min_price=min_price,
        max_price=max_price,
        min_year=min_year,
        max_year=max_year,
        min_seats=min_seats,
        status=status,
        available_from=available_from,
        available_to=available_to,
    )
    return await vehicle_service.list_vehicles(params, db)


@router.get("/{vehicle_id}", response_model=VehicleDetailResponse)
async def get_vehicle(vehicle_id: uuid.UUID, db: DbSession) -> VehicleDetailResponse:
    result = await vehicle_service.get_vehicle_detail(vehicle_id, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return result


@router.get("/{vehicle_id}/availability", response_model=AvailabilityResponse)
async def check_availability(
    vehicle_id: uuid.UUID,
    db: DbSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> AvailabilityResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be before end_date",
        )

    body = AvailabilityRequest(start_date=start_date, end_date=end_date)
    result = await vehicle_service.check_availability(vehicle_id, body, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return result
