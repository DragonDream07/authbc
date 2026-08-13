import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status
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
from app.db import get_db_connection


JWT_SECRET = os.environ.get("JWT_SECRET", "changeme")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS = int(os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30"))
RESET_TOKEN_EXPIRE_MINUTES = int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", "30"))
BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
REFRESH_COOKIE_NAME = "refresh_token"


def _hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _validate_password_strength(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")
    return errors


async def login(body: LoginRequest, response: Response) -> LoginResponse:
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, full_name, password_hash, is_active FROM users WHERE email = $1",
            body.email,
        )
        if not row or not _verify_password(body.password, row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "details": [],
                },
            )
        if not row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Invalid email or password.",
                    "details": [],
                },
            )

        user_id = str(row["id"])
        access_token = _create_access_token(user_id, row["email"])
        raw_refresh = secrets.token_hex(32)
        refresh_hash = _hash_sha256(raw_refresh)
        remember = body.rememberMe if body.rememberMe is not None else False
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)

        await conn.execute(
            """
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, remember_me, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, now())
            """,
            uuid.UUID(user_id),
            refresh_hash,
            expires_at,
            remember,
        )

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        expires=int(expires_at.timestamp()),
    )

    return LoginResponse(
        accessToken=access_token,
        tokenType="bearer",
        user=MeResponse(
            id=user_id,
            email=row["email"],
            fullName=row["full_name"],
        ),
    )


async def register(body: RegisterRequest) -> RegisterResponse:
    if body.password != body.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PASSWORD_MISMATCH",
                "message": "Passwords do not match.",
                "details": [],
            },
        )

    strength_errors = _validate_password_strength(body.password)
    if strength_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "WEAK_PASSWORD",
                "message": strength_errors[0],
                "details": strength_errors,
            },
        )

    password_hash = _hash_password(body.password)

    async with get_db_connection() as conn:
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "An account with this email already exists.",
                    "details": [],
                },
            )

        row = await conn.fetchrow(
            """
            INSERT INTO users (id, full_name, email, password_hash, is_active, created_at, updated_at)
            VALUES (gen_random_uuid(), $1, $2, $3, true, now(), now())
            RETURNING id, full_name, email
            """,
            body.fullName,
            body.email,
            password_hash,
        )

    return RegisterResponse(
        id=str(row["id"]),
        email=row["email"],
        fullName=row["full_name"],
    )


async def forgotPassword(body: ForgotPasswordRequest) -> ForgotPasswordResponse:
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1 AND is_active = true",
            body.email,
        )
        if row:
            raw_token = secrets.token_hex(32)
            token_hash = _hash_sha256(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

            await conn.execute(
                """
                INSERT INTO password_resets (id, user_id, token_hash, expires_at, created_at)
                VALUES (gen_random_uuid(), $1, $2, $3, now())
                """,
                row["id"],
                token_hash,
                expires_at,
            )
            # In a real system, send raw_token via email here.

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


async def resetPassword(body: ResetPasswordRequest) -> ResetPasswordResponse:
    if body.password != body.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "PASSWORD_MISMATCH",
                "message": "Passwords do not match.",
                "details": [],
            },
        )

    strength_errors = _validate_password_strength(body.password)
    if strength_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "WEAK_PASSWORD",
                "message": strength_errors[0],
                "details": strength_errors,
            },
        )

    token_hash = _hash_sha256(body.token)
    now = datetime.now(timezone.utc)

    async with get_db_connection() as conn:
        reset_row = await conn.fetchrow(
            """
            SELECT id, user_id, expires_at, used_at
            FROM password_resets
            WHERE token_hash = $1
            """,
            token_hash,
        )

        if not reset_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_RESET_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                },
            )

        if reset_row["used_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "RESET_TOKEN_USED",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                },
            )

        expires_at = reset_row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "RESET_TOKEN_EXPIRED",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                },
            )

        new_hash = _hash_password(body.password)
        user_id = reset_row["user_id"]

        await conn.execute(
            "UPDATE users SET password_hash = $1, updated_at = now() WHERE id = $2",
            new_hash,
            user_id,
        )

        await conn.execute(
            "UPDATE password_resets SET used_at = $1 WHERE id = $2",
            now,
            reset_row["id"],
        )

        # Revoke all existing refresh tokens for the user for security.
        await conn.execute(
            "UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = $1 AND revoked_at IS NULL",
            user_id,
        )

    return ResetPasswordResponse(
        message="Your password has been reset successfully."
    )


async def me(request: Request) -> MeResponse:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authentication required.",
                "details": [],
            },
        )
    token = auth_header[len("Bearer "):]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "TOKEN_EXPIRED",
                "message": "Authentication required.",
                "details": [],
            },
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Authentication required.",
                "details": [],
            },
        )

    user_id = payload.get("sub")
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, full_name, is_active FROM users WHERE id = $1",
            uuid.UUID(user_id),
        )
    if not row or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "Authentication required.",
                "details": [],
            },
        )
    return MeResponse(
        id=str(row["id"]),
        email=row["email"],
        fullName=row["full_name"],
    )


async def logout(body: LogoutRequest, response: Response) -> LogoutResponse:
    refresh_token = body.refreshToken if body.refreshToken else None
    if refresh_token:
        token_hash = _hash_sha256(refresh_token)
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE refresh_tokens SET revoked_at = now() WHERE token_hash = $1 AND revoked_at IS NULL",
                token_hash,
            )
    response.delete_cookie(key=REFRESH_COOKIE_NAME)
    return LogoutResponse(message="Logged out successfully.")


async def refresh(body: RefreshRequest, response: Response) -> RefreshResponse:
    raw_token = body.refreshToken
    token_hash = _hash_sha256(raw_token)
    now = datetime.now(timezone.utc)

    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked_at, rt.remember_me,
                   u.email, u.full_name, u.is_active
            FROM refresh_tokens rt
            JOIN users u ON u.id = rt.user_id
            WHERE rt.token_hash = $1
            """,
            token_hash,
        )

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Session is invalid or has expired.",
                    "details": [],
                },
            )

        if row["revoked_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "REFRESH_TOKEN_REVOKED",
                    "message": "Session is invalid or has expired.",
                    "details": [],
                },
            )

        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "REFRESH_TOKEN_EXPIRED",
                    "message": "Session is invalid or has expired.",
                    "details": [],
                },
            )

        if not row["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "ACCOUNT_INACTIVE",
                    "message": "Session is invalid or has expired.",
                    "details": [],
                },
            )

        # Revoke old token.
        await conn.execute(
            "UPDATE refresh_tokens SET revoked_at = now() WHERE id = $1",
            row["id"],
        )

        # Issue new tokens.
        user_id = str(row["user_id"])
        access_token = _create_access_token(user_id, row["email"])
        new_raw_refresh = secrets.token_hex(32)
        new_refresh_hash = _hash_sha256(new_raw_refresh)
        remember = row["remember_me"]
        expire_days = REFRESH_TOKEN_REMEMBER_DAYS if remember else REFRESH_TOKEN_EXPIRE_DAYS
        new_expires_at = now + timedelta(days=expire_days)

        await conn.execute(
            """
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, remember_me, created_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, now())
            """,
            uuid.UUID(user_id),
            new_refresh_hash,
            new_expires_at,
            remember,
        )

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_raw_refresh,
        httponly=True,
        samesite="lax",
        secure=True,
        expires=int(new_expires_at.timestamp()),
    )

    return RefreshResponse(
        accessToken=access_token,
        tokenType="bearer",
    )
