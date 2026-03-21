from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.core.email import send_password_reset_email, send_verification_email
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.db.session import DbSession
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services.auth_service import (
    forgot_password,
    login_user,
    logout_user,
    refresh_tokens,
    register_user,
    reset_password,
    verify_email,
)

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


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    try:
        return await login_user(body, db)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    try:
        return await refresh_tokens(body, db)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest) -> None:
    await logout_user(body)


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(
    db: DbSession,
    token: str = Query(...),
) -> MessageResponse:
    try:
        await verify_email(token, db)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    return MessageResponse(message="Email verified successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password_endpoint(
    body: ForgotPasswordRequest,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    token = await forgot_password(body, db)
    if token is not None:
        background_tasks.add_task(send_password_reset_email, body.email, token)
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    body: ResetPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    try:
        await reset_password(body, db)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return MessageResponse(message="Password has been reset successfully")
