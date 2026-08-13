import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import PasswordReset, RefreshToken, User

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "changeme")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER", "30")
)
BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
PASSWORD_RESET_EXPIRE_MINUTES = int(
    os.environ.get("PASSWORD_RESET_EXPIRE_MINUTES", "60")
)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number."
    return None


class AuthService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def register(self, body: RegisterRequest) -> RegisterResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        strength_error = _validate_password_strength(body.password)
        if strength_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": strength_error,
                        "details": [{"field": "password", "message": strength_error}],
                    }
                },
            )

        result = await self.db.execute(select(User).where(User.email == body.email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "EMAIL_TAKEN",
                        "message": "An account with this email already exists.",
                        "details": [{"field": "email", "message": "An account with this email already exists."}],
                    }
                },
            )

        user = User(
            full_name=body.full_name,
            email=body.email,
            password_hash=_hash_password(body.password),
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        access_token = _create_access_token(user.id)
        return RegisterResponse(
            accessToken=access_token,
            user=MeResponse(
                id=str(user.id),
                fullName=user.full_name,
                email=user.email,
                createdAt=user.created_at.isoformat(),
            ),
        )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        result = await self.db.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()

        invalid_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": [],
                }
            },
        )

        if user is None or not _verify_password(body.password, user.password_hash):
            raise invalid_error

        if not user.is_active:
            raise invalid_error

        access_token = _create_access_token(user.id)

        remember = body.remember_me or False
        expire_days = REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER if remember else REFRESH_TOKEN_EXPIRE_DAYS
        raw_refresh = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

        rt = RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh),
            expires_at=expires_at,
            remember_me=remember,
        )
        self.db.add(rt)
        await self.db.commit()

        response.set_cookie(
            key="refresh_token",
            value=raw_refresh,
            httponly=True,
            samesite="lax",
            secure=True,
            max_age=int(timedelta(days=expire_days).total_seconds()),
            path="/",
        )

        return LoginResponse(
            accessToken=access_token,
            user=MeResponse(
                id=str(user.id),
                fullName=user.full_name,
                email=user.email,
                createdAt=user.created_at.isoformat(),
            ),
        )

    async def forgotPassword(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        result = await self.db.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()

        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(64)
            token_hash = _hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=PASSWORD_RESET_EXPIRE_MINUTES
            )

            pr = PasswordReset(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            self.db.add(pr)
            await self.db.commit()

            reset_link = f"{FRONTEND_URL}/reset-password?token={raw_token}"
            # In production, send reset_link via email.
            # Logging omitted to avoid leaking the token.

        return ForgotPasswordResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )

    async def resetPassword(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [{"field": "confirmPassword", "message": "Passwords do not match."}],
                    }
                },
            )

        strength_error = _validate_password_strength(body.password)
        if strength_error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": strength_error,
                        "details": [{"field": "password", "message": strength_error}],
                    }
                },
            )

        token_hash = _hash_token(body.token)
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.used_at.is_(None),
                PasswordReset.expires_at > now,
            )
        )
        pr = result.scalar_one_or_none()

        invalid_token_error = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                }
            },
        )

        if pr is None:
            raise invalid_token_error

        user_result = await self.db.execute(select(User).where(User.id == pr.user_id))
        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise invalid_token_error

        user.password_hash = _hash_password(body.password)
        pr.used_at = now
        await self.db.commit()

        return ResetPasswordResponse(message="Your password has been reset successfully. You can now log in.")

    async def me(self, credentials: Optional[HTTPAuthorizationCredentials]) -> MeResponse:
        token = credentials.credentials if credentials else None
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id or payload.get("type") != "access":
                raise JWTError()
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired token.",
                        "details": [],
                    }
                },
            )

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        return MeResponse(
            id=str(user.id),
            fullName=user.full_name,
            email=user.email,
            createdAt=user.created_at.isoformat(),
        )

    async def logout(
        self,
        body: LogoutRequest,
        credentials: Optional[HTTPAuthorizationCredentials],
        response: Response,
    ) -> LogoutResponse:
        if body.refresh_token:
            token_hash = _hash_token(body.refresh_token)
            now = datetime.now(timezone.utc)
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            rt = result.scalar_one_or_none()
            if rt is not None:
                rt.revoked_at = now
                await self.db.commit()

        response.delete_cookie(key="refresh_token", path="/")
        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self,
        credentials: Optional[HTTPAuthorizationCredentials],
        response: Response,
    ) -> RefreshResponse:
        raw_token = credentials.credentials if credentials else None
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Refresh token required.",
                        "details": [],
                    }
                },
            )

        token_hash = _hash_token(raw_token)
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        rt = result.scalar_one_or_none()

        if rt is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired refresh token.",
                        "details": [],
                    }
                },
            )

        rt.revoked_at = now

        remember = rt.remember_me or False
        expire_days = REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER if remember else REFRESH_TOKEN_EXPIRE_DAYS
        new_raw = secrets.token_urlsafe(64)
        new_expires_at = now + timedelta(days=expire_days)

        new_rt = RefreshToken(
            user_id=rt.user_id,
            token_hash=_hash_token(new_raw),
            expires_at=new_expires_at,
            remember_me=remember,
        )
        self.db.add(new_rt)
        await self.db.commit()

        user_result = await self.db.execute(select(User).where(User.id == rt.user_id))
        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required.",
                        "details": [],
                    }
                },
            )

        access_token = _create_access_token(user.id)

        response.set_cookie(
            key="refresh_token",
            value=new_raw,
            httponly=True,
            samesite="lax",
            secure=True,
            max_age=int(timedelta(days=expire_days).total_seconds()),
            path="/",
        )

        return RefreshResponse(
            accessToken=access_token,
            user=MeResponse(
                id=str(user.id),
                fullName=user.full_name,
                email=user.email,
                createdAt=user.created_at.isoformat(),
            ),
        )
