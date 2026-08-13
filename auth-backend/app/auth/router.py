from fastapi import APIRouter

from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutResponse,
    RefreshResponse,
)
from app.auth.service import (
    register,
    login,
    forgotPassword,
    resetPassword,
    me,
    logout,
    refresh,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register_endpoint(body: RegisterRequest) -> RegisterResponse:
    return await register(body)


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login_endpoint(body: LoginRequest) -> LoginResponse:
    return await login(body)


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=202)
async def forgot_password_endpoint(body: ForgotPasswordRequest) -> ForgotPasswordResponse:
    return await forgotPassword(body)


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=200)
async def reset_password_endpoint(body: ResetPasswordRequest) -> ResetPasswordResponse:
    return await resetPassword(body)


@router.get("/me", response_model=MeResponse, status_code=200)
async def me_endpoint() -> MeResponse:
    return await me()


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout_endpoint() -> LogoutResponse:
    return await logout()


@router.post("/refresh", response_model=RefreshResponse, status_code=200)
async def refresh_endpoint() -> RefreshResponse:
    return await refresh()
