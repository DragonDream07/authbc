from __future__ import annotations

from pydantic import AnyUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str = Field(..., description="Secret used to sign JWTs")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = Field(
        ..., description="Access token lifetime in minutes"
    )

    # ------------------------------------------------------------------ #
    # Bcrypt
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = Field(
        ..., ge=12, description="Bcrypt work factor (minimum 12)"
    )

    # ------------------------------------------------------------------ #
    # Password reset
    # ------------------------------------------------------------------ #
    RESET_TOKEN_TTL_MINUTES: int = Field(
        ..., description="Password-reset token lifetime in minutes"
    )

    # ------------------------------------------------------------------ #
    # Refresh tokens
    # ------------------------------------------------------------------ #
    REFRESH_TOKEN_TTL_DAYS: int = Field(
        ..., description="Refresh token lifetime in days (normal session)"
    )
    REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME: int = Field(
        ..., description="Refresh token lifetime in days when remember-me is set"
    )

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = Field(..., description="SMTP server hostname")
    SMTP_PORT: int = Field(..., description="SMTP server port")
    SMTP_USER: str = Field(..., description="SMTP authentication username")
    SMTP_PASSWORD: str = Field(..., description="SMTP authentication password")
    SMTP_FROM_EMAIL: EmailStr = Field(
        ..., description="Envelope sender address for outgoing mail"
    )
    SMTP_TLS: bool = Field(default=True, description="Use STARTTLS for SMTP")

    # ------------------------------------------------------------------ #
    # Rate limits
    # ------------------------------------------------------------------ #
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = Field(
        ..., description="Max login attempts per window"
    )
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(
        ..., description="Login rate-limit window in seconds"
    )
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = Field(
        ..., description="Max forgot-password requests per window"
    )
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = Field(
        ..., description="Forgot-password rate-limit window in seconds"
    )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("BCRYPT_ROUNDS")
    @classmethod
    def bcrypt_rounds_must_be_secure(cls, value: int) -> int:
        if value < 12:
            raise ValueError(
                "BCRYPT_ROUNDS must be at least 12 to satisfy the security policy."
            )
        return value

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("JWT_SECRET_KEY must not be empty.")
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL must not be empty.")
        return value


# Instantiate once; the application imports this singleton.
# Validation runs at import time — fails fast on any missing or invalid var.
settings: Settings = Settings()
