from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.leaderboard.schemas import LeaderboardEntry
from src.leaderboard.services import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get(
    "",
    response_model=list[LeaderboardEntry],
    response_model_by_alias=True,
    summary="Tabla de posiciones",
    response_description="Ranking de participantes ordenado por puntos totales",
)
async def get_leaderboard(
    limit: int = Query(
        50,
        ge=1,
        le=200,
        description="Cantidad máxima de participantes a devolver",
        examples=[50],
    ),
    db: AsyncSession = Depends(get_db),
) -> list[LeaderboardEntry]:
    """
    Devuelve la tabla de posiciones global de la quiniela.

    Los puntos se calculan automáticamente cuando un admin finaliza un partido
    via `POST /admin/matches/{id}/finalize`.

    **Sistema de puntos:**
    - Marcador exacto: **3 puntos**
    - Resultado correcto (G/E/P): **1 punto**
    - Incorrecto: **0 puntos**

    Este endpoint es **público** — no requiere autenticación.
    """
    return await LeaderboardService(db).get_leaderboard(limit=limit)
