from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Response

from app.auth.schemas import LoginRequest, LoginResponse
from app.db import get_db_connection


# ---------------------------------------------------------------------------
# Environment / config
# ---------------------------------------------------------------------------

JWT_SECRET: str = os.environ["JWT_SECRET"]
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

# Enumeration-safe error message (must match validation-rules verbatim)
_INVALID_CREDENTIALS_MSG = "Invalid email or password."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _create_access_token(user_id: int, email: str) -> str:
    expire = _now_utc() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------


async def login(payload: LoginRequest, response: Response) -> LoginResponse:
    """Authenticate a user and return an access token.

    On failure always raises with the same generic message to prevent
    email enumeration (NFR-03).
    """
    from fastapi import HTTPException, status

    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, full_name, password_hash, is_active
            FROM users
            WHERE email = $1
            """,
            payload.email.lower(),
        )

    # Enumeration resistance: perform a dummy check even when user not found
    if row is None:
        # Run a dummy bcrypt to keep timing consistent
        bcrypt.checkpw(b"dummy", bcrypt.hashpw(b"dummy", bcrypt.gensalt(BCRYPT_ROUNDS)))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": _INVALID_CREDENTIALS_MSG,
                    "details": {},
                }
            },
        )

    password_valid = _verify_password(payload.password, row["password_hash"])

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": _INVALID_CREDENTIALS_MSG,
                    "details": {},
                }
            },
        )

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": _INVALID_CREDENTIALS_MSG,
                    "details": {},
                }
            },
        )

    access_token = _create_access_token(
        user_id=row["id"],
        email=row["email"],
    )

    return LoginResponse(
        accessToken=access_token,
        tokenType="bearer",
        expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
