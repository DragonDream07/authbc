from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address.")
    password: str = Field(..., min_length=1, description="User's password.")


class LoginResponse(BaseModel):
    accessToken: str = Field(..., description="JWT access token.")
    tokenType: str = Field(..., description="Token type, e.g. 'bearer'.")
    expiresIn: int = Field(..., description="Access token lifetime in seconds.")
