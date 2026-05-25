"""Router zleceń serwisowych (`/service-orders`).

Panel technika:

* ``POST /service-orders``                — utworzenie nowego zlecenia
* ``GET  /service-orders``                — listing z filtrami i paginacją
* ``GET  /service-orders/stats``          — liczniki dla kart podsumowania
* ``GET  /service-orders/{id}``           — szczegóły z historią
* ``PUT  /service-orders/{id}``           — edycja zlecenia (poza statusem)
* ``PUT  /service-orders/{id}/status``    — zmiana statusu (state machine)
* ``POST /service-orders/{id}/history``   — dopis do historii prac
* ``GET  /vehicles/{id}/service-orders``  — timeline serwisów per pojazd
  (dla widoku „historia serwisowa pojazdu")
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.deps import CurrentUser, require_roles
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.service import (
    PaginatedServiceOrderResponse,
    ServiceHistoryCreate,
    ServiceOrderCreate,
    ServiceOrderDetailResponse,
    ServiceOrderListItem,
    ServiceOrderListParams,
    ServiceOrderStats,
    ServiceOrderStatusUpdate,
    ServiceOrderUpdate,
    VehicleServiceTimelineResponse,
)
from app.services import service_order_service

router = APIRouter(prefix="/service-orders", tags=["service-orders"])

TechnicianOrAdmin = Annotated[User, Depends(require_roles(UserRole.TECHNICIAN, UserRole.ADMIN))]


@router.post(
    "",
    response_model=ServiceOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new service order",
)
async def create_service_order(
    body: ServiceOrderCreate,
    db: DbSession,
    current_user: TechnicianOrAdmin,
) -> ServiceOrderDetailResponse:
    order = await service_order_service.create_order(db, current_user, body)
    return ServiceOrderDetailResponse.model_validate(order)


@router.get(
    "",
    response_model=PaginatedServiceOrderResponse,
    summary="List service orders (filtered/paginated)",
)
async def list_service_orders(
    db: DbSession,
    current_user: TechnicianOrAdmin,
    params: Annotated[ServiceOrderListParams, Query()],
) -> PaginatedServiceOrderResponse:
    orders, total = await service_order_service.list_orders(db, current_user, params)
    return PaginatedServiceOrderResponse(
        items=[ServiceOrderListItem.model_validate(o) for o in orders],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get(
    "/stats",
    response_model=ServiceOrderStats,
    summary="Aggregate counts (scheduled / in_progress / completed / total)",
)
async def get_service_order_stats(
    db: DbSession,
    _: TechnicianOrAdmin,
) -> ServiceOrderStats:
    return await service_order_service.get_stats(db)


@router.get(
    "/{order_id}",
    response_model=ServiceOrderDetailResponse,
    summary="Get a single service order with vehicle/technician/history",
)
async def get_service_order(
    order_id: Annotated[uuid.UUID, Path()],
    db: DbSession,
    _: TechnicianOrAdmin,
) -> ServiceOrderDetailResponse:
    order = await service_order_service.get_order(db, order_id)
    return ServiceOrderDetailResponse.model_validate(order)


@router.put(
    "/{order_id}",
    response_model=ServiceOrderDetailResponse,
    summary="Update an open service order (type / description / cost / scheduled date)",
)
async def update_service_order(
    order_id: Annotated[uuid.UUID, Path()],
    body: ServiceOrderUpdate,
    db: DbSession,
    current_user: TechnicianOrAdmin,
) -> ServiceOrderDetailResponse:
    order = await service_order_service.update_order(db, current_user, order_id, body)
    return ServiceOrderDetailResponse.model_validate(order)


@router.put(
    "/{order_id}/status",
    response_model=ServiceOrderDetailResponse,
    summary="Advance a service order through SCHEDULED -> IN_PROGRESS -> COMPLETED",
)
async def update_service_order_status(
    order_id: Annotated[uuid.UUID, Path()],
    body: ServiceOrderStatusUpdate,
    db: DbSession,
    current_user: TechnicianOrAdmin,
) -> ServiceOrderDetailResponse:
    order = await service_order_service.update_status(db, current_user, order_id, body)
    return ServiceOrderDetailResponse.model_validate(order)


@router.post(
    "/{order_id}/history",
    response_model=ServiceOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record executed work (notes, parts replaced, mileage at service)",
)
async def add_service_history_entry(
    order_id: Annotated[uuid.UUID, Path()],
    body: ServiceHistoryCreate,
    db: DbSession,
    current_user: TechnicianOrAdmin,
) -> ServiceOrderDetailResponse:
    # Defensive: keep URL and body in sync.
    body = body.model_copy(update={"service_order_id": order_id})
    order = await service_order_service.add_history_entry(db, current_user, body)
    return ServiceOrderDetailResponse.model_validate(order)


# ---------------------------------------------------------------------------
# Vehicle-centric timeline view
# ---------------------------------------------------------------------------

vehicle_router = APIRouter(prefix="/vehicles", tags=["service-orders", "vehicles"])


@vehicle_router.get(
    "/{vehicle_id}/service-orders",
    response_model=VehicleServiceTimelineResponse,
    summary="Service timeline for a vehicle (newest scheduled first)",
)
async def list_vehicle_service_timeline(
    vehicle_id: Annotated[uuid.UUID, Path()],
    db: DbSession,
    _: TechnicianOrAdmin,
) -> VehicleServiceTimelineResponse:
    orders = await service_order_service.list_vehicle_timeline(db, vehicle_id)
    return VehicleServiceTimelineResponse(
        vehicle_id=vehicle_id,
        orders=[ServiceOrderListItem.model_validate(o) for o in orders],
    )
