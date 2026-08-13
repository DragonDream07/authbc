from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., alias="fullName")
    email: EmailStr
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")
    terms_accepted: bool = Field(..., alias="termsAccepted")

    model_config = {"populate_by_name": True}


class RegisterResponse(BaseModel):
    id: str
    fullName: str
    email: str
    createdAt: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    rememberMe: Optional[bool] = False


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str = Field(..., alias="confirmPassword")

    model_config = {"populate_by_name": True}


class ResetPasswordResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    id: str
    fullName: str
    email: str
    createdAt: str


class LogoutRequest(BaseModel):
    refreshToken: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
    refreshToken: Optional[str] = None


class RefreshResponse(BaseModel):
    accessToken: str
    tokenType: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
