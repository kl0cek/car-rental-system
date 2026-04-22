import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status

from app.core.deps import CurrentUser, require_roles
from app.core.email import send_reservation_confirmed_email
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.reservation import (
    CreateReservationRequest,
    PaginatedReservationResponse,
    ReservationListParams,
    ReservationResponse,
)
from app.services import reservation_service

router = APIRouter(prefix="/reservations", tags=["reservations"])

EmployeeOrAdmin = Annotated[User, Depends(require_roles(UserRole.EMPLOYEE, UserRole.ADMIN))]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_reservation(
    body: CreateReservationRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ReservationResponse:
    reservation = await reservation_service.create_reservation(db, current_user, body)
    return ReservationResponse.model_validate(reservation)


@router.get("")
async def list_reservations(
    db: DbSession,
    current_user: CurrentUser,
    params: Annotated[ReservationListParams, Query()],
) -> PaginatedReservationResponse:
    reservations, total = await reservation_service.list_user_reservations(db, current_user, params)
    return PaginatedReservationResponse(
        items=[ReservationResponse.model_validate(r) for r in reservations],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.put("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: Annotated[uuid.UUID, Path()],
    db: DbSession,
    current_user: CurrentUser,
) -> ReservationResponse:
    reservation = await reservation_service.cancel_reservation(db, current_user, reservation_id)
    return ReservationResponse.model_validate(reservation)


@router.put("/{reservation_id}/confirm")
async def confirm_reservation(
    reservation_id: Annotated[uuid.UUID, Path()],
    db: DbSession,
    current_user: EmployeeOrAdmin,
    background_tasks: BackgroundTasks,
) -> ReservationResponse:
    reservation, email_data = await reservation_service.confirm_reservation(db, reservation_id)
    background_tasks.add_task(
        send_reservation_confirmed_email,
        to_email=email_data.to_email,
        first_name=email_data.first_name,
        vehicle_name=email_data.vehicle_name,
        start_date=email_data.start_date,
        end_date=email_data.end_date,
        total_price=email_data.total_price,
    )
    return ReservationResponse.model_validate(reservation)
