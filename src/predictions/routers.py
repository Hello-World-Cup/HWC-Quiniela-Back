from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.predictions.schemas import PredictionCreate, PredictionResponse
from src.predictions.services import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post(
    "",
    response_model=PredictionResponse,
    response_model_by_alias=True,
    status_code=201,
    summary="Crear o actualizar pronóstico",
    response_description="Pronóstico guardado con todos sus detalles",
    responses={
        403: {"description": "El plazo para pronosticar este partido ya cerró"},
        404: {"description": "Partido no encontrado"},
    },
)
async def create_or_update_prediction(
    payload: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    """
    Crea o actualiza el pronóstico del usuario autenticado para un partido.

    **Reglas:**
    - Solo se puede pronosticar antes del cierre (`prediction_deadline` o `kickoff` si no hay deadline)
    - Si ya existe un pronóstico para ese partido, se actualiza (upsert)
    - Devuelve **403** si el plazo ya cerró, incluso si se intenta actualizar un pronóstico anterior

    Requiere header: `Authorization: Bearer <token>`
    """
    prediction = await PredictionService(db).upsert_prediction(current_user.id, payload)
    return PredictionResponse.from_orm_prediction(prediction)


@router.get(
    "/me",
    response_model=list[PredictionResponse],
    response_model_by_alias=True,
    summary="Mis pronósticos",
    response_description="Lista de todos los pronósticos del usuario autenticado",
)
async def get_my_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionResponse]:
    """
    Devuelve todos los pronósticos realizados por el usuario autenticado,
    incluyendo el detalle del partido y los puntos obtenidos (si el partido ya terminó).

    Requiere header: `Authorization: Bearer <token>`
    """
    predictions = await PredictionService(db).get_user_predictions(current_user.id)
    return [PredictionResponse.from_orm_prediction(p) for p in predictions]
