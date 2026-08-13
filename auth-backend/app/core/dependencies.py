from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer access token and return the authenticated User.

    Raises:
        HTTPException 401: if the token is missing, malformed, expired, or the
            referenced user does not exist or is inactive.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_TOKEN",
                "message": "Could not validate credentials.",
                "details": None,
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: str = credentials.credentials

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _unauthorized

    subject: str | None = payload.get("sub")
    if subject is None:
        raise _unauthorized

    user: User | None = db.query(User).filter(User.id == subject).first()
    if user is None:
        raise _unauthorized

    if not user.is_active:
        raise _unauthorized

    return user
