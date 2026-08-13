import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    MeResponse,
    LogoutResponse,
    RefreshResponse,
)

# ---------------------------------------------------------------------------
# Configuration (read from environment with safe defaults for development)
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "changeme-secret")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", "12"))

# ---------------------------------------------------------------------------
# In-memory stores (replace with real DB repositories in production)
# These mirror the schema: users, password_resets, refresh_tokens
# ---------------------------------------------------------------------------
_users: dict[str, dict] = {}          # keyed by email
_users_by_id: dict[str, dict] = {}    # keyed by id
_refresh_tokens: list[dict] = []      # list of refresh_token records
_password_resets: list[dict] = []     # list of password_reset records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _make_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _make_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def _validate_password_policy(password: str) -> list[str]:
    """Return list of violated rule messages (empty = policy satisfied)."""
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


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def register(body: RegisterRequest) -> RegisterResponse:
    # Validate full_name
    if not body.fullName or not body.fullName.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Full name is required.",
                    "details": [{"field": "fullName", "message": "Full name is required."}],
                }
            },
        )

    # Validate email presence
    if not body.email or not body.email.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Email is required.",
                    "details": [{"field": "email", "message": "Email is required."}],
                }
            },
        )

    # Validate email format (basic)
    import re
    email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    if not email_pattern.match(body.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Enter a valid email address.",
                    "details": [{"field": "email", "message": "Enter a valid email address."}],
                }
            },
        )

    # Validate password presence
    if not body.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Password is required.",
                    "details": [{"field": "password", "message": "Password is required."}],
                }
            },
        )

    # Validate password policy
    policy_errors = _validate_password_policy(body.password)
    if policy_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": policy_errors[0],
                    "details": [{"field": "password", "message": msg} for msg in policy_errors],
                }
            },
        )

    # Validate confirm_password presence
    if not body.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Please confirm your password.",
                    "details": [{"field": "confirmPassword", "message": "Please confirm your password."}],
                }
            },
        )

    # Validate passwords match
    if body.password != body.confirmPassword:
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

    # Validate terms acceptance
    if not body.acceptTerms:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "You must accept the Terms of Service.",
                    "details": [{"field": "acceptTerms", "message": "You must accept the Terms of Service."}],
                }
            },
        )

    # Check duplicate email
    email_lower = body.email.strip().lower()
    if email_lower in _users:
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

    # Create user record
    user_id = secrets.token_urlsafe(16)
    now = datetime.now(timezone.utc)
    password_hash = _hash_password(body.password)

    user_record = {
        "id": user_id,
        "full_name": body.fullName.strip(),
        "email": email_lower,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    _users[email_lower] = user_record
    _users_by_id[user_id] = user_record

    # Issue tokens
    access_token = _make_access_token(user_id, email_lower)
    raw_refresh = _make_refresh_token()
    refresh_expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    _refresh_tokens.append({
        "id": secrets.token_urlsafe(16),
        "user_id": user_id,
        "token_hash": _sha256(raw_refresh),
        "expires_at": refresh_expires,
        "revoked_at": None,
        "remember_me": False,
        "created_at": now,
    })

    return RegisterResponse(
        accessToken=access_token,
        refreshToken=raw_refresh,
        user={
            "id": user_id,
            "fullName": user_record["full_name"],
            "email": user_record["email"],
            "isActive": user_record["is_active"],
            "createdAt": now.isoformat(),
        },
    )


async def login(body: LoginRequest) -> LoginResponse:
    email_lower = (body.email or "").strip().lower()
    user = _users.get(email_lower)

    # Enumeration-resistant: always same error
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

    if user is None:
        raise invalid_exc

    if not _verify_password(body.password or "", user["password_hash"]):
        raise invalid_exc

    if not user["is_active"]:
        raise invalid_exc

    now = datetime.now(timezone.utc)
    access_token = _make_access_token(user["id"], email_lower)
    raw_refresh = _make_refresh_token()
    remember = body.rememberMe if body.rememberMe is not None else False
    refresh_days = REFRESH_TOKEN_EXPIRE_DAYS * (2 if remember else 1)
    refresh_expires = now + timedelta(days=refresh_days)

    _refresh_tokens.append({
        "id": secrets.token_urlsafe(16),
        "user_id": user["id"],
        "token_hash": _sha256(raw_refresh),
        "expires_at": refresh_expires,
        "revoked_at": None,
        "remember_me": remember,
        "created_at": now,
    })

    return LoginResponse(
        accessToken=access_token,
        refreshToken=raw_refresh,
        user={
            "id": user["id"],
            "fullName": user["full_name"],
            "email": user["email"],
            "isActive": user["is_active"],
            "createdAt": user["created_at"].isoformat(),
        },
    )


async def forgotPassword(body: ForgotPasswordRequest) -> ForgotPasswordResponse:
    # Enumeration-resistant: always return the same message
    email_lower = (body.email or "").strip().lower()
    user = _users.get(email_lower)

    if user is not None and user["is_active"]:
        raw_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        _password_resets.append({
            "id": secrets.token_urlsafe(16),
            "user_id": user["id"],
            "token_hash": _sha256(raw_token),
            "expires_at": expires,
            "used_at": None,
            "created_at": now,
        })
        # In production: send email with raw_token link

    return ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


async def resetPassword(body: ResetPasswordRequest) -> ResetPasswordResponse:
    if not body.token or not body.token.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Reset token is required.",
                    "details": [{"field": "token", "message": "Reset token is required."}],
                }
            },
        )

    policy_errors = _validate_password_policy(body.password or "")
    if policy_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": policy_errors[0],
                    "details": [{"field": "password", "message": msg} for msg in policy_errors],
                }
            },
        )

    if body.password != body.confirmPassword:
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

    token_hash = _sha256(body.token.strip())
    now = datetime.now(timezone.utc)
    reset_record = None
    for rec in _password_resets:
        if (
            rec["token_hash"] == token_hash
            and rec["used_at"] is None
            and rec["expires_at"] > now
        ):
            reset_record = rec
            break

    if reset_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                }
            },
        )

    user = _users_by_id.get(reset_record["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_OR_EXPIRED_TOKEN",
                    "message": "This password reset link is invalid or has expired.",
                    "details": [],
                }
            },
        )

    # Update password
    user["password_hash"] = _hash_password(body.password)
    user["updated_at"] = now
    reset_record["used_at"] = now

    # Revoke all refresh tokens for this user
    for rt in _refresh_tokens:
        if rt["user_id"] == user["id"] and rt["revoked_at"] is None:
            rt["revoked_at"] = now

    return ResetPasswordResponse(message="Your password has been reset successfully.")


async def me() -> MeResponse:
    # Placeholder: real implementation would decode the Authorization header JWT
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


async def logout() -> LogoutResponse:
    # Placeholder: real implementation would revoke the refresh token from the cookie/header
    return LogoutResponse(message="Logged out successfully.")


async def refresh() -> RefreshResponse:
    # Placeholder: real implementation would rotate the refresh token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_REFRESH_TOKEN",
                "message": "Invalid or expired refresh token.",
                "details": [],
            }
        },
    )
