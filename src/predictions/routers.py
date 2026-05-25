from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.predictions.schemas import PredictionCreate, PredictionResponse
from src.predictions.services import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse, status_code=201)
async def create_or_update_prediction(
    payload: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    return await PredictionService(db).upsert_prediction(current_user.id, payload)


@router.get("/me", response_model=list[PredictionResponse])
async def get_my_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionResponse]:
    return await PredictionService(db).get_user_predictions(current_user.id)
