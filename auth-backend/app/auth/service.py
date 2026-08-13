import hashlib
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable must be set.")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_REMEMBER_DAYS: int = int(
    os.environ.get("REFRESH_TOKEN_REMEMBER_DAYS", "30")
)
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))
REFRESH_COOKIE_NAME: str = "refresh_token"

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _create_refresh_token_value() -> str:
    return hashlib.sha256(os.urandom(64)).hexdigest()


def _set_refresh_cookie(
    response: Response, token_value: str, remember_me: bool
) -> None:
    max_age = (
        REFRESH_TOKEN_REMEMBER_DAYS * 86400
        if remember_me
        else REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token_value,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=max_age,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/auth/refresh",
    )


async def _get_db():
    """Return an asyncpg connection from the pool."""
    import asyncpg  # type: ignore

    conn = await asyncpg.connect(DATABASE_URL)
    return conn


class AuthService:
    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    async def register(self, body: RegisterRequest) -> RegisterResponse:
        import asyncpg  # type: ignore

        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [
                            {
                                "field": "confirmPassword",
                                "message": "Passwords do not match.",
                            }
                        ],
                    }
                },
            )

        self._validate_password_strength(body.password)

        conn = await _get_db()
        try:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", body.email.lower()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "EMAIL_TAKEN",
                            "message": (
                                "An account with this email already exists."
                            ),
                            "details": [
                                {
                                    "field": "email",
                                    "message": (
                                        "An account with this email already"
                                        " exists."
                                    ),
                                }
                            ],
                        }
                    },
                )

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            row = await conn.fetchrow(
                """
                INSERT INTO users (full_name, email, password_hash, is_active)
                VALUES ($1, $2, $3, TRUE)
                RETURNING id, full_name, email, created_at
                """,
                body.full_name,
                body.email.lower(),
                password_hash,
            )

            return RegisterResponse(
                id=str(row["id"]),
                full_name=row["full_name"],
                email=row["email"],
                created_at=row["created_at"].isoformat(),
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------
    async def login(self, body: LoginRequest, response: Response) -> LoginResponse:
        conn = await _get_db()
        try:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, password_hash, is_active"
                " FROM users WHERE email = $1",
                body.email.lower(),
            )

            invalid_exc = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "details": [],
                    }
                },
            )

            if not row:
                raise invalid_exc

            if not bcrypt.checkpw(
                body.password.encode(), row["password_hash"].encode()
            ):
                raise invalid_exc

            if not row["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "ACCOUNT_INACTIVE",
                            "message": "Your account is inactive.",
                            "details": [],
                        }
                    },
                )

            access_token = _create_access_token(str(row["id"]), row["email"])
            refresh_token_value = _create_refresh_token_value()
            remember_me: bool = getattr(body, "remember_me", False) or False

            expires_at = datetime.now(timezone.utc) + timedelta(
                days=(
                    REFRESH_TOKEN_REMEMBER_DAYS
                    if remember_me
                    else REFRESH_TOKEN_EXPIRE_DAYS
                )
            )

            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, remember_me)
                VALUES ($1, $2, $3, $4)
                """,
                row["id"],
                _hash_token(refresh_token_value),
                expires_at,
                remember_me,
            )

            _set_refresh_cookie(response, refresh_token_value, remember_me)

            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                user=MeResponse(
                    id=str(row["id"]),
                    full_name=row["full_name"],
                    email=row["email"],
                ),
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # forgotPassword
    # ------------------------------------------------------------------
    async def forgotPassword(
        self, body: ForgotPasswordRequest
    ) -> ForgotPasswordResponse:
        conn = await _get_db()
        try:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 AND is_active = TRUE",
                body.email.lower(),
            )

            if row:
                raw_token = hashlib.sha256(os.urandom(64)).hexdigest()
                token_hash = _hash_token(raw_token)
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

                await conn.execute(
                    """
                    INSERT INTO password_resets (user_id, token_hash, expires_at)
                    VALUES ($1, $2, $3)
                    """,
                    row["id"],
                    token_hash,
                    expires_at,
                )
                # In production, send email with raw_token here.

            return ForgotPasswordResponse(
                message=(
                    "If an account with that email exists, a password reset"
                    " link has been sent."
                )
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # resetPassword
    # ------------------------------------------------------------------
    async def resetPassword(
        self, body: ResetPasswordRequest
    ) -> ResetPasswordResponse:
        if body.password != body.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Passwords do not match.",
                        "details": [
                            {
                                "field": "confirmPassword",
                                "message": "Passwords do not match.",
                            }
                        ],
                    }
                },
            )

        self._validate_password_strength(body.password)

        conn = await _get_db()
        try:
            token_hash = _hash_token(body.token)
            now = datetime.now(timezone.utc)

            row = await conn.fetchrow(
                """
                SELECT pr.id, pr.user_id, pr.expires_at, pr.used_at
                FROM password_resets pr
                WHERE pr.token_hash = $1
                """,
                token_hash,
            )

            invalid_exc = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "INVALID_RESET_TOKEN",
                        "message": (
                            "This password reset link is invalid or has"
                            " expired."
                        ),
                        "details": [],
                    }
                },
            )

            if not row:
                raise invalid_exc

            if row["used_at"] is not None:
                raise invalid_exc

            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                raise invalid_exc

            password_hash = bcrypt.hashpw(
                body.password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            ).decode()

            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET password_hash = $1,"
                    " updated_at = NOW() WHERE id = $2",
                    password_hash,
                    row["user_id"],
                )
                await conn.execute(
                    "UPDATE password_resets SET used_at = NOW() WHERE id = $1",
                    row["id"],
                )
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = NOW()"
                    " WHERE user_id = $1 AND revoked_at IS NULL",
                    row["user_id"],
                )

            return ResetPasswordResponse(
                message="Your password has been reset successfully."
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # me
    # ------------------------------------------------------------------
    async def me(self, token: str) -> MeResponse:
        payload = self._decode_access_token(token)
        user_id = payload.get("sub")

        conn = await _get_db()
        try:
            row = await conn.fetchrow(
                "SELECT id, full_name, email, is_active FROM users WHERE id = $1",
                int(user_id),
            )
            if not row or not row["is_active"]:
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
                id=str(row["id"]),
                full_name=row["full_name"],
                email=row["email"],
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------
    async def logout(
        self, token: str | None, request: Request, response: Response
    ) -> None:
        refresh_token_value: str | None = request.cookies.get(REFRESH_COOKIE_NAME)

        if refresh_token_value:
            conn = await _get_db()
            try:
                token_hash = _hash_token(refresh_token_value)
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = NOW()"
                    " WHERE token_hash = $1 AND revoked_at IS NULL",
                    token_hash,
                )
            finally:
                await conn.close()

        _clear_refresh_cookie(response)

    # ------------------------------------------------------------------
    # refresh  (FR-08)
    # ------------------------------------------------------------------
    async def refresh(self, request: Request, response: Response) -> RefreshResponse:
        refresh_token_value: str | None = request.cookies.get(REFRESH_COOKIE_NAME)

        unauthorized_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is missing, invalid, or expired.",
                    "details": [],
                }
            },
        )

        if not refresh_token_value:
            raise unauthorized_exc

        token_hash = _hash_token(refresh_token_value)
        now = datetime.now(timezone.utc)

        conn = await _get_db()
        try:
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
                raise unauthorized_exc

            if row["revoked_at"] is not None:
                raise unauthorized_exc

            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                raise unauthorized_exc

            if not row["is_active"]:
                raise unauthorized_exc

            # Rotate: revoke old token and issue a new one
            new_refresh_token_value = _create_refresh_token_value()
            new_token_hash = _hash_token(new_refresh_token_value)
            remember_me: bool = row["remember_me"] or False
            new_expires_at = now + timedelta(
                days=(
                    REFRESH_TOKEN_REMEMBER_DAYS
                    if remember_me
                    else REFRESH_TOKEN_EXPIRE_DAYS
                )
            )

            async with conn.transaction():
                await conn.execute(
                    "UPDATE refresh_tokens SET revoked_at = $1 WHERE id = $2",
                    now,
                    row["id"],
                )
                await conn.execute(
                    """
                    INSERT INTO refresh_tokens
                        (user_id, token_hash, expires_at, remember_me)
                    VALUES ($1, $2, $3, $4)
                    """,
                    row["user_id"],
                    new_token_hash,
                    new_expires_at,
                    remember_me,
                )

            access_token = _create_access_token(str(row["user_id"]), row["email"])
            _set_refresh_cookie(response, new_refresh_token_value, remember_me)

            return RefreshResponse(
                access_token=access_token,
                token_type="bearer",
            )
        finally:
            await conn.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": "Access token has expired.",
                        "details": [],
                    }
                },
            )
        except jwt.PyJWTError:
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
        if payload.get("type") != "access":
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
        return payload

    def _validate_password_strength(self, password: str) -> None:
        errors = []
        if len(password) < 8:
            errors.append(
                {
                    "field": "password",
                    "message": "Password must be at least 8 characters.",
                }
            )
        if not any(c.isupper() for c in password):
            errors.append(
                {
                    "field": "password",
                    "message": "Password must contain at least one uppercase letter.",
                }
            )
        if not any(c.islower() for c in password):
            errors.append(
                {
                    "field": "password",
                    "message": "Password must contain at least one lowercase letter.",
                }
            )
        if not any(c.isdigit() for c in password):
            errors.append(
                {
                    "field": "password",
                    "message": "Password must contain at least one number.",
                }
            )
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Password does not meet the requirements.",
                        "details": errors,
                    }
                },
            )
