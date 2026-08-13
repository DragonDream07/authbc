from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Password policy constants (mirrored from capabilities.yaml)
# ---------------------------------------------------------------------------

PASSWORD_MIN_LENGTH = 8
_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")

# Email validation regex — compiled once at module load
_EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Exact validation messages from validation-rules.md
# These strings must not be paraphrased, reworded, or translated.
# ---------------------------------------------------------------------------

MSG_FULL_NAME_REQUIRED = "Full name is required."
MSG_FULL_NAME_MAX_LENGTH = "Full name must not exceed 100 characters."

MSG_EMAIL_REQUIRED = "Email is required."
MSG_EMAIL_INVALID = "Enter a valid email address."
MSG_EMAIL_MAX_LENGTH = "Email must not exceed 254 characters."
MSG_EMAIL_TAKEN = "An account with this email already exists."

MSG_PASSWORD_REQUIRED = "Password is required."
MSG_PASSWORD_MIN_LENGTH = "Password must be at least 8 characters."
MSG_PASSWORD_UPPERCASE = "Password must contain at least one uppercase letter."
MSG_PASSWORD_LOWERCASE = "Password must contain at least one lowercase letter."
MSG_PASSWORD_NUMBER = "Password must contain at least one number."

MSG_CONFIRM_PASSWORD_REQUIRED = "Please confirm your password."
MSG_CONFIRM_PASSWORD_MISMATCH = "Passwords do not match."

MSG_TERMS_REQUIRED = "You must accept the terms and conditions."

MSG_LOGIN_INVALID = "Invalid email or password."

MSG_TOKEN_INVALID = "This reset link is invalid or has already been used."
MSG_TOKEN_EXPIRED = "This reset link has expired. Please request a new one."


# ---------------------------------------------------------------------------
# Individual field validators
# Each raises ValueError with the exact message when validation fails.
# Return the (possibly coerced) value on success.
# ---------------------------------------------------------------------------


def validate_full_name(value: str | None) -> str:
    """Validate the full_name field.

    Rules (applied in order):
    1. Required — MSG_FULL_NAME_REQUIRED
    2. Max length 100 — MSG_FULL_NAME_MAX_LENGTH
    """
    if not value or not value.strip():
        raise ValueError(MSG_FULL_NAME_REQUIRED)
    value = value.strip()
    if len(value) > 100:
        raise ValueError(MSG_FULL_NAME_MAX_LENGTH)
    return value


def validate_email(value: str | None) -> str:
    """Validate the email field.

    Rules (applied in order):
    1. Required — MSG_EMAIL_REQUIRED
    2. Max length 254 — MSG_EMAIL_MAX_LENGTH
    3. Format (basic RFC-5322 local@domain) — MSG_EMAIL_INVALID
    """
    if not value or not value.strip():
        raise ValueError(MSG_EMAIL_REQUIRED)
    value = value.strip()
    if len(value) > 254:
        raise ValueError(MSG_EMAIL_MAX_LENGTH)
    if not _EMAIL_RE.match(value):
        raise ValueError(MSG_EMAIL_INVALID)
    return value.lower()


def validate_password(value: str | None) -> str:
    """Validate the password field against the active password policy.

    Rules (applied in order):
    1. Required — MSG_PASSWORD_REQUIRED
    2. Minimum length 8 — MSG_PASSWORD_MIN_LENGTH
    3. At least one uppercase letter — MSG_PASSWORD_UPPERCASE
    4. At least one lowercase letter — MSG_PASSWORD_LOWERCASE
    5. At least one number — MSG_PASSWORD_NUMBER

    Note: require_special_character is false in capabilities.yaml;
    no special-character rule is applied here.
    """
    if not value:
        raise ValueError(MSG_PASSWORD_REQUIRED)
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(MSG_PASSWORD_MIN_LENGTH)
    if not _UPPER_RE.search(value):
        raise ValueError(MSG_PASSWORD_UPPERCASE)
    if not _LOWER_RE.search(value):
        raise ValueError(MSG_PASSWORD_LOWERCASE)
    if not _DIGIT_RE.search(value):
        raise ValueError(MSG_PASSWORD_NUMBER)
    return value


def validate_confirm_password(password: str, confirm_password: str | None) -> str:
    """Validate that confirm_password matches password.

    Rules (applied in order):
    1. Required — MSG_CONFIRM_PASSWORD_REQUIRED
    2. Must match password — MSG_CONFIRM_PASSWORD_MISMATCH
    """
    if not confirm_password:
        raise ValueError(MSG_CONFIRM_PASSWORD_REQUIRED)
    if confirm_password != password:
        raise ValueError(MSG_CONFIRM_PASSWORD_MISMATCH)
    return confirm_password


def validate_terms_accepted(value: bool | None) -> bool:
    """Validate that the user has accepted the terms and conditions.

    Rules (applied in order):
    1. Must be True — MSG_TERMS_REQUIRED
    """
    if not value:
        raise ValueError(MSG_TERMS_REQUIRED)
    return value


# ---------------------------------------------------------------------------
# Composite password-policy checker (returns list of failing rule messages)
# Used by the service layer to build structured error details.
# ---------------------------------------------------------------------------


def check_password_policy(password: str) -> list[str]:
    """Return a list of violated password-policy messages (in rule order).

    An empty list means the password passes all active rules.
    This helper does NOT raise; callers decide how to surface failures.
    """
    errors: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(MSG_PASSWORD_MIN_LENGTH)
    if not _UPPER_RE.search(password):
        errors.append(MSG_PASSWORD_UPPERCASE)
    if not _LOWER_RE.search(password):
        errors.append(MSG_PASSWORD_LOWERCASE)
    if not _DIGIT_RE.search(password):
        errors.append(MSG_PASSWORD_NUMBER)
    return errors
