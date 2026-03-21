from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.email import send_verification_email
from app.core.exceptions import EmailAlreadyRegisteredError
from app.db.session import DbSession
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.auth_service import register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> RegisterResponse:
    try:
        user, token = await register_user(body, db)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    background_tasks.add_task(send_verification_email, user.email, token)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_verified=user.is_verified,
        created_at=user.created_at,
        message="Registration successful. Please check your email to verify your account.",
    )
