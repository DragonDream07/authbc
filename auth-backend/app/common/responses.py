from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse

from app.common.errors import AppException, ErrorCode


def error_response(
    code: ErrorCode,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Shape an error payload into the standard envelope and return a JSONResponse."""
    body: Dict[str, Any] = {
        "error": {
            "code": code.value,
            "message": message,
            "details": details or {},
        }
    }
    return JSONResponse(status_code=status_code, content=body)


def exception_to_response(exc: AppException) -> JSONResponse:
    """Convert an AppException directly to a JSONResponse using the error envelope."""
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
