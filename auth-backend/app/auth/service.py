from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Response
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_reset_repo: PasswordResetRepository,
    ) -> None:
        self._session = session
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._password_reset_repo = password_reset_repo

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        existing = await self._user_repo.get_by_email(body.email)
        if existing is not None:
            raise ConflictError(
                code="EMAIL_TAKEN",
                message="An account with this email already exists.",
            )

        password_hash = _hash_password(body.password)
        user = await self._user_repo.create(
            full_name=body.full_name,
            email=body.email,
            password_hash=password_hash,
        )
        return RegisterResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        user = await self._user_repo.get_by_email(body.email)
        if user is None or not _verify_password(body.password, user.password_hash):
            raise AuthenticationError(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        if not user.is_active:
            raise AuthenticationError(
                code="ACCOUNT_INACTIVE",
                message="Invalid email or password.",
            )

        access_token = _create_access_token(user.id, user.email)

        raw_refresh = secrets.token_urlsafe(64)
        token_hash = _hash_token(raw_refresh)
        remember_me: bool = body.remember_me if body.remember_me is not None else False
        expire_days = (
            settings.REFRESH_TOKEN_REMEMBER_DAYS
            if remember_me
            else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

        await self._refresh_token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            remember_me=remember_me,
        )

        _set_refresh_cookie(response, raw_refresh, expires_at)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            id=user.id,
            full_name=user.full_name,
            email=user.email,
        )

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = await self._user_repo.get_by_email(body.email)
        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(64)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
            )
            await self._password_reset_repo.create(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            # Email sending is handled by a background task / mailer outside this service.
            # The raw_token would be passed to the mailer here in a full implementation.

        return ForgotPasswordResponse(
            message="If that email address is in our system, we emailed a password reset link."
        )

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        token_hash = _hash_token(body.token)
        reset_record = await self._password_reset_repo.get_valid_by_hash(token_hash)

        if reset_record is None:
            raise ValidationError(
                code="INVALID_RESET_TOKEN",
                message="This password reset link is invalid or has expired.",
            )

        new_hash = _hash_password(body.password)
        await self._user_repo.update_password(reset_record.user_id, new_hash)
        await self._password_reset_repo.mark_used(reset_record.id)
        await self._refresh_token_repo.revoke_all_for_user(reset_record.user_id)

        return ResetPasswordResponse(message="Your password has been reset successfully.")

    # ------------------------------------------------------------------
    # me  (thin — router handles it directly via get_current_user)
    # ------------------------------------------------------------------
    async def me(self, current_user_id: int) -> MeResponse:  # pragma: no cover
        user = await self._user_repo.get_by_id(current_user_id)
        if user is None:
            raise NotFoundError(code="USER_NOT_FOUND", message="User not found.")
        return MeResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(self, body: LogoutRequest, response: Response) -> LogoutResponse:
        if body.refresh_token:
            token_hash = _hash_token(body.refresh_token)
            await self._refresh_token_repo.revoke_by_hash(token_hash)

        _clear_refresh_cookie(response)
        return LogoutResponse(message="Logged out successfully.")

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------
    async def refresh(self, body: RefreshRequest, response: Response) -> RefreshResponse:
        token_hash = _hash_token(body.refresh_token)
        record = await self._refresh_token_repo.get_valid_by_hash(token_hash)

        if record is None:
            raise AuthenticationError(
                code="INVALID_REFRESH_TOKEN",
                message="Refresh token is invalid or has expired.",
            )

        user = await self._user_repo.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(
                code="INVALID_REFRESH_TOKEN",
                message="Refresh token is invalid or has expired.",
            )

        # Rotate: revoke old token
        await self._refresh_token_repo.revoke_by_hash(token_hash)

        # Issue new refresh token
        raw_refresh = secrets.token_urlsafe(64)
        new_hash = _hash_token(raw_refresh)
        expire_days = (
            settings.REFRESH_TOKEN_REMEMBER_DAYS
            if record.remember_me
            else settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
        await self._refresh_token_repo.create(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=expires_at,
            remember_me=record.remember_me,
        )

        access_token = _create_access_token(user.id, user.email)
        _set_refresh_cookie(response, raw_refresh, expires_at)

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
        )


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------

def _set_refresh_cookie(response: Response, raw_token: str, expires_at: datetime) -> None:
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/auth/refresh",
    )
