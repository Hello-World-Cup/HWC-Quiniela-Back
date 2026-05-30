from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import GoogleLoginRequest, TokenResponse
from src.auth.services import AuthService
from src.core.database import get_db
from src.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/google",
    response_model=TokenResponse,
    response_model_by_alias=True,
    summary="Login con Google",
    response_description="JWT de acceso para usar en endpoints protegidos",
)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Valida un **Google ID Token** y devuelve un JWT del backend.

    El frontend debe:
    1. Obtener el `id_token` de Google via NextAuth.js
    2. Enviarlo en el body de esta petición
    3. Guardar el `access_token` devuelto
    4. Incluirlo como `Authorization: Bearer <token>` en peticiones protegidas

    El token tiene una validez de **7 días**.
    """
    try:
        user = await AuthService(db).get_or_create_user_from_google(payload.token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
