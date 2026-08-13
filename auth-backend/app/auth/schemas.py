from typing import List, Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str


class MeResponse(BaseModel):
    id: str
    fullName: str
    email: str
    createdAt: str


class RegisterResponse(BaseModel):
    accessToken: str
    user: MeResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class LoginResponse(BaseModel):
    accessToken: str
    user: MeResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str


class ResetPasswordResponse(BaseModel):
    message: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    accessToken: str
    user: MeResponse


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail]


class ErrorResponse(BaseModel):
    error: ErrorBody
