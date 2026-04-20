from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, status

from app.core.deps import CurrentUser
from app.core.email import send_verification_email
from app.core.exceptions import EmailAlreadyRegisteredError
from app.db.session import DbSession
from app.schemas.user import (
    AvatarUploadResponse,
    PaginatedUserRentalsResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserRentalsListParams,
)
from app.services import rental_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: CurrentUser) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_me(
    body: UserProfileUpdate,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> UserProfileResponse:
    try:
        user, verification_token = await user_service.update_profile(db, current_user, body)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    if verification_token is not None:
        background_tasks.add_task(send_verification_email, user.email, verification_token)
    return UserProfileResponse.model_validate(user)


@router.post("/me/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    db: DbSession,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File()],
) -> AvatarUploadResponse:
    user = await user_service.upload_avatar(db, current_user, file)
    assert user.avatar_url is not None
    return AvatarUploadResponse(avatar_url=user.avatar_url)


@router.get("/me/rentals", response_model=PaginatedUserRentalsResponse)
async def list_my_rentals(
    db: DbSession,
    current_user: CurrentUser,
    params: Annotated[UserRentalsListParams, Query()],
) -> PaginatedUserRentalsResponse:
    rentals, total = await user_service.list_user_rentals(db, current_user, params)
    return PaginatedUserRentalsResponse(
        items=[rental_service.build_user_rental_item(r) for r in rentals],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )
