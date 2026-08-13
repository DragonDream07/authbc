from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.auth.service import (
    login,
    register,
    forgotPassword,
    resetPassword,
    me,
    logout,
    refresh,
)
from typing import Any

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_endpoint(body: LoginRequest, response: Response) -> Any:
    return await login(body, response)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_endpoint(body: RegisterRequest) -> Any:
    return await register(body)


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password_endpoint(body: ForgotPasswordRequest) -> Any:
    return await forgotPassword(body)


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
async def reset_password_endpoint(body: ResetPasswordRequest) -> Any:
    return await resetPassword(body)


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me_endpoint(request: Request) -> Any:
    return await me(request)


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout_endpoint(body: LogoutRequest, response: Response) -> Any:
    return await logout(body, response)


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_endpoint(body: RefreshRequest, response: Response) -> Any:
    return await refresh(body, response)
