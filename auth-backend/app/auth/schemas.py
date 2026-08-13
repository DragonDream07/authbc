from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str
    confirm_password: str


class RegisterResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class MeResponse(BaseModel):
    id: str
    full_name: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: MeResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str


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
