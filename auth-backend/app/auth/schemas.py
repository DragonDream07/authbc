from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = None


class MeResponse(BaseModel):
    id: str
    email: str
    fullName: str


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str
    user: MeResponse


class RegisterRequest(BaseModel):
    fullName: str
    email: EmailStr
    password: str
    confirmPassword: str


class RegisterResponse(BaseModel):
    id: str
    email: str
    fullName: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirmPassword: str


class ResetPasswordResponse(BaseModel):
    message: str


class LogoutRequest(BaseModel):
    refreshToken: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    refreshToken: str


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
