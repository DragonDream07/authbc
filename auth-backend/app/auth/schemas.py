from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    confirmPassword: str
    acceptTerms: bool


class UserPayload(BaseModel):
    id: str
    fullName: str
    email: str
    isActive: bool
    createdAt: str


class RegisterResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserPayload


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: bool | None = None


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserPayload


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Reset Password
# ---------------------------------------------------------------------------


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirmPassword: str


class ResetPasswordResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


class MeResponse(BaseModel):
    user: UserPayload


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class LogoutResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


class RefreshResponse(BaseModel):
    accessToken: str
    refreshToken: str


# ---------------------------------------------------------------------------
# Shared error envelope (used by exception handlers)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    error: ErrorBody
