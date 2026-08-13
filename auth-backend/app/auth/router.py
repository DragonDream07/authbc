from fastapi import APIRouter, Response, status

from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
)
from app.auth.service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    operation_id="login",
)
async def login_endpoint(
    payload: LoginRequest,
    response: Response,
) -> LoginResponse:
    return await login(payload=payload, response=response)
