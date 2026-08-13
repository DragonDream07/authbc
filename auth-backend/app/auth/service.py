from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Response, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

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
from app.models.password_reset import PasswordReset
from app.models.refresh_token import RefreshToken
from app.models.user import User

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/authdb",
)
JWT_SECRET: str = os.environ.get("JWT_SECRET", "changeme")
JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)
REFRESH_TOKEN_REMEMBER_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE", "true").lower() == "true"

_engine = create_async_engine(DATABASE_URL, echo=False)
_async_session: sessionmaker = sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_access_token(user_id: str, email: str) -> str:
    expire = _now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": _now(),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _make_refresh_token_value() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )


def _set_refresh_cookie(response: Response, token_value: str, remember_me: bool) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key="refresh_token",
        value=token_value,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=max_age,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/auth",
    )


class AuthService:
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        async with _async_session() as session:
            result = await session.execute(
                select(User).where(User.email == body.email.lower())
            )
            existing = result.scalar_one_or_none()
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "EMAIL_TAKEN",
                            "message": "An account with this email already exists.",
                            "details": {},
                        }
                    },
                )

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            user = User(
                full_name=body.full_name,
                email=body.email.lower(),
                password_hash=password_hash,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            return RegisterResponse(
                id=str(user.id),
                fullName=user.full_name,
                email=user.email,
                createdAt=user.created_at.isoformat(),
            )

    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        async with _async_session() as session:
            result = await session.execute(
                select(User).where(User.email == body.email.lower())
            )
            user: Optional[User] = result.scalar_one_or_none()

            invalid_exc = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": {},
                    }
                },
            )

            if user is None:
                raise invalid_exc

            if not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
                raise invalid_exc

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": "Your account is inactive.",
                            "details": {},
                        }
                    },
                )

            access_token = _make_access_token(str(user.id), user.email)
            refresh_value = _make_refresh_token_value()
            remember_me: bool = body.rememberMe if body.rememberMe is not None else False
            expire_days = (
                REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            )
            refresh_token = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(refresh_value),
                expires_at=_now() + timedelta(days=expire_days),
                revoked_at=None,
                remember_me=remember_me,
            )
            session.add(refresh_token)
            await session.commit()

            _set_refresh_cookie(response, refresh_value, remember_me)

            return LoginResponse(
                accessToken=access_token,
                tokenType="Bearer",
            )

    async def forgotPassword(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        async with _async_session() as session:
            result = await session.execute(
                select(User).where(User.email == body.email.lower())
            )
            user: Optional[User] = result.scalar_one_or_none()

            if user is not None and user.is_active:
                raw_token = hashlib.sha256(os.urandom(64)).hexdigest()
                token_hash = _hash_token(raw_token)
                reset = PasswordReset(
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=_now() + timedelta(hours=1),
                    used_at=None,
                )
                session.add(reset)
                await session.commit()
                # In a real system we would send an email here with raw_token.

            return ForgotPasswordResponse(
                message="If an account with that email exists, a password reset link has been sent."
            )

    async def resetPassword(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        async with _async_session() as session:
            token_hash = _hash_token(body.token)
            result = await session.execute(
                select(PasswordReset).where(
                    and_(
                        PasswordReset.token_hash == token_hash,
                        PasswordReset.used_at.is_(None),
                        PasswordReset.expires_at > _now(),
                    )
                )
            )
            reset: Optional[PasswordReset] = result.scalar_one_or_none()

            if reset is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_OR_EXPIRED_TOKEN",
                            "message": "This password reset link is invalid or has expired.",
                            "details": {},
                        }
                    },
                )

            user_result = await session.execute(
                select(User).where(User.id == reset.user_id)
            )
            user: Optional[User] = user_result.scalar_one_or_none()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_OR_EXPIRED_TOKEN",
                            "message": "This password reset link is invalid or has expired.",
                            "details": {},
                        }
                    },
                )

            new_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()
            user.password_hash = new_hash
            user.updated_at = _now()
            reset.used_at = _now()
            session.add(user)
            session.add(reset)
            await session.commit()

            return ResetPasswordResponse(
                message="Your password has been reset successfully."
            )

    async def me(self, access_token: str) -> MeResponse:
        payload = _decode_access_token(access_token)
        user_id = payload.get("sub")

        async with _async_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user: Optional[User] = result.scalar_one_or_none()

            if user is None or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive.",
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
        access_token: Optional[str],
        response: Response,
    ) -> LogoutResponse:
        async with _async_session() as session:
            refresh_token_value: Optional[str] = body.refreshToken if body else None

            if refresh_token_value:
                token_hash = _hash_token(refresh_token_value)
                result = await session.execute(
                    select(RefreshToken).where(
                        and_(
                            RefreshToken.token_hash == token_hash,
                            RefreshToken.revoked_at.is_(None),
                        )
                    )
                )
                refresh_token_record: Optional[RefreshToken] = result.scalar_one_or_none()
                if refresh_token_record is not None:
                    refresh_token_record.revoked_at = _now()
                    session.add(refresh_token_record)
                    await session.commit()

        _clear_refresh_cookie(response)

        return LogoutResponse(message="Logged out successfully.")

    async def refresh(
        self, body: RefreshRequest, response: Response
    ) -> RefreshResponse:
        refresh_token_value: Optional[str] = body.refreshToken if body else None

        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "MISSING_REFRESH_TOKEN",
                        "message": "Refresh token is required.",
                        "details": {},
                    }
                },
            )

        token_hash = _hash_token(refresh_token_value)

        async with _async_session() as session:
            result = await session.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.token_hash == token_hash,
                        RefreshToken.revoked_at.is_(None),
                        RefreshToken.expires_at > _now(),
                    )
                )
            )
            record: Optional[RefreshToken] = result.scalar_one_or_none()

            if record is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": {
                            "code": "INVALID_REFRESH_TOKEN",
                            "message": "Refresh token is invalid or has expired.",
                            "details": {},
                        }
                    },
                )

            # Revoke old token (rotation)
            record.revoked_at = _now()
            session.add(record)

            user_result = await session.execute(
                select(User).where(User.id == record.user_id)
            )
            user: Optional[User] = user_result.scalar_one_or_none()

            if user is None or not user.is_active:
                await session.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive.",
                )

            new_access_token = _make_access_token(str(user.id), user.email)
            new_refresh_value = _make_refresh_token_value()
            remember_me: bool = record.remember_me or False
            expire_days = (
                REFRESH_TOKEN_REMEMBER_DAYS if remember_me else REFRESH_TOKEN_EXPIRE_DAYS
            )
            new_refresh_record = RefreshToken(
                user_id=user.id,
                token_hash=_hash_token(new_refresh_value),
                expires_at=_now() + timedelta(days=expire_days),
                revoked_at=None,
                remember_me=remember_me,
            )
            session.add(new_refresh_record)
            await session.commit()

            _set_refresh_cookie(response, new_refresh_value, remember_me)

            return RefreshResponse(
                accessToken=new_access_token,
                tokenType="Bearer",
            )
