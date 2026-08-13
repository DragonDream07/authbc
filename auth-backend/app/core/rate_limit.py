from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

# ---------------------------------------------------------------------------
# Shared limiter instance (keyed by client IP)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Reusable limit strings sourced from settings (NFR-08)
# ---------------------------------------------------------------------------

# Applied to POST /auth/login
LOGIN_LIMIT: str = settings.LOGIN_RATE_LIMIT

# Applied to POST /auth/forgot-password
FORGOT_PASSWORD_LIMIT: str = settings.FORGOT_PASSWORD_RATE_LIMIT
