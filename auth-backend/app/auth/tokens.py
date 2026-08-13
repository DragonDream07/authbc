from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config.settings import settings

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

REFRESH_TOKEN_TTL: timedelta = timedelta(
    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
)

REFRESH_TOKEN_TTL_EXTENDED: timedelta = timedelta(
    days=settings.REFRESH_TOKEN_EXPIRE_DAYS_EXTENDED
)

RESET_TOKEN_TTL: timedelta = timedelta(
    minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
)

# ---------------------------------------------------------------------------
# Raw token generation
# ---------------------------------------------------------------------------


def _generate_raw_token(nbytes: int = 32) -> str:
    """Return a URL-safe random token string."""
    return secrets.token_urlsafe(nbytes)


def hash_token(raw: str) -> str:
    """Return the SHA-256 hex digest of *raw*.

    All refresh and reset tokens are stored hashed; incoming values are
    hashed before lookup so the plaintext never touches the database.
    """
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Access token (JWT)
# ---------------------------------------------------------------------------


def create_access_token(
    *,
    user_id: int,
    email: str,
    ttl: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    The token carries ``sub`` (user_id as string), ``email``, and ``exp``.
    TTL defaults to *ACCESS_TOKEN_TTL*.
    """
    expire = datetime.now(tz=timezone.utc) + (ttl or ACCESS_TOKEN_TTL)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token.

    Raises ``jose.JWTError`` (or a subclass) if the token is invalid or
    expired — callers must handle this.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def get_user_id_from_token(token: str) -> Optional[int]:
    """Return the integer user_id from a valid access token, or None."""
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


def create_refresh_token(
    *, remember_me: bool = False
) -> tuple[str, str, datetime]:
    """Generate a refresh token.

    Returns ``(raw_token, token_hash, expires_at)``.

    When *remember_me* is ``True`` the token lives for
    *REFRESH_TOKEN_TTL_EXTENDED* (longer session); otherwise the standard
    *REFRESH_TOKEN_TTL* applies.
    """
    raw = _generate_raw_token()
    token_hash = hash_token(raw)
    ttl = REFRESH_TOKEN_TTL_EXTENDED if remember_me else REFRESH_TOKEN_TTL
    expires_at = datetime.now(tz=timezone.utc) + ttl
    return raw, token_hash, expires_at


def is_refresh_token_valid(token_row: dict) -> bool:
    """Return ``True`` iff the refresh token row is neither revoked nor expired."""
    if token_row.get("revoked_at") is not None:
        return False
    expires_at: datetime = token_row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc) < expires_at


# ---------------------------------------------------------------------------
# Password-reset token
# ---------------------------------------------------------------------------


def create_reset_token() -> tuple[str, str, datetime]:
    """Generate a one-time password-reset token.

    Returns ``(raw_token, token_hash, expires_at)``.
    """
    raw = _generate_raw_token()
    token_hash = hash_token(raw)
    expires_at = datetime.now(tz=timezone.utc) + RESET_TOKEN_TTL
    return raw, token_hash, expires_at


def is_reset_token_valid(reset_row: dict) -> tuple[bool, str]:
    """Check whether a password-reset row is still usable.

    Returns ``(is_valid, reason)`` where *reason* is ``"ok"``, ``"used"``,
    or ``"expired"``.
    """
    if reset_row.get("used_at") is not None:
        return False, "used"
    expires_at: datetime = reset_row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(tz=timezone.utc) >= expires_at:
        return False, "expired"
    return True, "ok"


# ---------------------------------------------------------------------------
# Rotation helper (stateless portion)
# ---------------------------------------------------------------------------


def prepare_rotated_refresh_token(
    *, remember_me: bool = False
) -> tuple[str, str, datetime]:
    """Generate replacement refresh-token material for rotation.

    Identical to ``create_refresh_token``; exists as a named alias so call
    sites in the service layer communicate intent clearly.
    """
    return create_refresh_token(remember_me=remember_me)
