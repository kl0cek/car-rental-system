from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_roles
from app.db.session import DbSession
from app.models.user import User, UserRole
from app.schemas.user import (
    AdminReservationItem,
    AdminReservationListParams,
    AdminUserItem,
    AdminUserListParams,
    PaginatedAdminReservationsResponse,
    PaginatedAdminUsersResponse,
)
from app.services import user_service

router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


@router.get("/reservations", response_model=PaginatedAdminReservationsResponse)
async def list_admin_reservations(
    db: DbSession,
    _: AdminUser,
    params: Annotated[AdminReservationListParams, Query()],
) -> PaginatedAdminReservationsResponse:
    reservations, total = await user_service.list_admin_reservations(db, params)
    return PaginatedAdminReservationsResponse(
        items=[AdminReservationItem.model_validate(r) for r in reservations],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/users", response_model=PaginatedAdminUsersResponse)
async def list_admin_users(
    db: DbSession,
    _: AdminUser,
    params: Annotated[AdminUserListParams, Query()],
) -> PaginatedAdminUsersResponse:
    users, total = await user_service.list_admin_users(db, params)
    return PaginatedAdminUsersResponse(
        items=[AdminUserItem.model_validate(u) for u in users],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )
