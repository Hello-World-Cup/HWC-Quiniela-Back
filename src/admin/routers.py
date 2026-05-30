from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.schemas import BaseSchema
from src.matches.schemas import MatchResponse
from src.scoring.service import ScoringService

router = APIRouter(prefix="/admin", tags=["admin"])


class FinalizeMatchRequest(BaseSchema):
    result_a: int = Field(ge=0, description="Goles del equipo local (team_a)", examples=[2])
    result_b: int = Field(ge=0, description="Goles del equipo visitante (team_b)", examples=[1])


@router.post(
    "/matches/{match_id}/finalize",
    response_model=MatchResponse,
    response_model_by_alias=True,
    summary="Finalizar partido y calcular puntos",
    response_description="Partido actualizado con el resultado final",
    responses={
        404: {"description": "Partido no encontrado"},
    },
)
async def finalize_match(
    match_id: int,
    payload: FinalizeMatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """
    Registra el resultado final de un partido y **calcula automáticamente los puntos**
    para todos los pronósticos de ese partido.

    **Acciones que realiza:**
    1. Actualiza `result_a` y `result_b` en el partido
    2. Cambia el estado a `finished`
    3. Itera todos los pronósticos del partido y asigna `points_awarded`:
       - Marcador exacto → 3 puntos
       - Resultado correcto (G/E/P) → 1 punto
       - Incorrecto → 0 puntos

    Después de llamar a este endpoint, `/leaderboard` reflejará los nuevos puntos.

    Requiere header: `Authorization: Bearer <token>`

    > ⚠️ Este endpoint no tiene protección de rol admin. En producción se recomienda
    > agregar una verificación de `current_user.is_admin` o un token especial de admin.
    """
    match = await ScoringService(db).finalize_match(
        match_id=match_id,
        result_a=payload.result_a,
        result_b=payload.result_b,
    )
    return MatchResponse.from_orm_match(match)
