from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import GoogleLoginRequest, TokenResponse
from src.auth.services import AuthService
from src.core.database import get_db
from src.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        user = await AuthService(db).get_or_create_user_from_google(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
