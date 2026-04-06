from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.deps import CurrentUser
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
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    UserResponse,
)
from app.services.auth_service import (
    forgot_password,
    login_user,
    logout_user_tokens,
    refresh_tokens,
    register_user,
    reset_password,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_OPTS: dict[str, Any] = {
    "httponly": True,
    "samesite": "lax",
    "secure": not settings.DEBUG,
    "path": "/",
}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **COOKIE_OPTS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **COOKIE_OPTS,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


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


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest, db: DbSession, response: Response) -> UserResponse:
    try:
        tokens, user = await login_user(body, db)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=UserResponse)
async def refresh(request: Request, db: DbSession, response: Response) -> UserResponse | Response:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    try:
        tokens, user = await refresh_tokens(RefreshRequest(refresh_token=refresh_token), db)
    except InvalidTokenError:
        error_response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired refresh token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
        _clear_auth_cookies(error_response)
        return error_response

    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    await logout_user_tokens(access_token, refresh_token)
    _clear_auth_cookies(response)


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
