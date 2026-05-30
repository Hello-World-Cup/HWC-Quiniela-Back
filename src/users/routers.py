from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.predictions.schemas import PredictionResponse
from src.predictions.services import PredictionService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/{user_id}/predictions",
    response_model=list[PredictionResponse],
    response_model_by_alias=True,
    summary="Pronósticos de un usuario",
    response_description="Lista de pronósticos del usuario especificado, con detalle del partido",
)
async def get_user_predictions(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionResponse]:
    """
    Devuelve todos los pronósticos de un usuario específico.

    Útil para ver el detalle de un participante desde la tabla de posiciones.
    Cualquier usuario autenticado puede consultar los pronósticos de cualquier otro.

    - `user_id` corresponde al campo `userId` de `LeaderboardEntry`

    Requiere header: `Authorization: Bearer <token>`
    """
    predictions = await PredictionService(db).get_user_predictions(int(user_id))
    return [PredictionResponse.from_orm_prediction(p) for p in predictions]
