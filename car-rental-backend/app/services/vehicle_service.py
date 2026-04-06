import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mongodb import get_mongo_db
from app.repositories import vehicle_repository
from app.schemas.vehicle import (
    AvailabilityRequest,
    AvailabilityResponse,
    PaginatedVehicleResponse,
    VehicleDetailResponse,
    VehicleListItem,
    VehicleListParams,
)


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

    booked_dates = await vehicle_repository.get_booked_dates(db, vehicle_id)

    average_rating, review_count = await _get_review_stats(vehicle_id)

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


async def check_availability(
    vehicle_id: uuid.UUID,
    body: AvailabilityRequest,
    db: AsyncSession,
) -> AvailabilityResponse | None:
    vehicle = await vehicle_repository.get_by_id(db, vehicle_id)
    if vehicle is None:
        return None

    conflicts = await vehicle_repository.count_conflicting_rentals(
        db, vehicle_id, body.start_date, body.end_date
    )

    return AvailabilityResponse(
        vehicle_id=vehicle_id,
        available=conflicts == 0,
        start_date=body.start_date,
        end_date=body.end_date,
        conflicting_rentals=conflicts,
    )


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
