from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config.settings import settings


# ---------------------------------------------------------------------------
# bcrypt helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    rounds: int = settings.BCRYPT_ROUNDS
    hashed: bytes = bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=rounds))
    return hashed.decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored bcrypt *hashed* value."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# SHA-256 token helpers  (for refresh tokens and password-reset tokens)
# ---------------------------------------------------------------------------

def hash_token(token: str) -> str:
    """Return the hex-encoded SHA-256 digest of *token*."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT access token.

    Args:
        subject: The ``sub`` claim — typically the user's UUID / id as a string.
        extra_claims: Additional claims merged into the payload.
        expires_delta: Override the default expiry from settings.

    Returns:
        A signed JWT string.
    """
    now = datetime.now(tz=timezone.utc)
    delta = expires_delta if expires_delta is not None else timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = now + delta

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*.

    Raises:
        jose.JWTError: if the token is invalid, expired, or the signature does
            not match.

    Returns:
        The decoded claims dictionary.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


def decode_access_token_unverified(token: str) -> dict[str, Any]:
    """Decode *token* **without** verifying the signature or expiry.

    Use only for debugging / logging — never for authorisation decisions.
    """
    return jwt.get_unverified_claims(token)
