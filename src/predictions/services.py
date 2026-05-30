from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.matches.models import Match
from src.matches.services import MatchService
from src.predictions.models import Prediction
from src.predictions.schemas import PredictionCreate


class PredictionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _assert_deadline(self, match: Match) -> None:
        cutoff = match.prediction_deadline if match.prediction_deadline is not None else match.start_time
        if datetime.now(UTC) >= cutoff:
            raise HTTPException(
                status_code=403,
                detail="El periodo para realizar pronósticos ha cerrado",
            )

    async def upsert_prediction(self, user_id: int, data: PredictionCreate) -> Prediction:
        match_id = int(data.match_id)
        match = await MatchService(self.db).get_match_by_id(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Partido no encontrado")

        self._assert_deadline(match)

        result = await self.db.execute(
            select(Prediction).where(
                Prediction.user_id == user_id,
                Prediction.match_id == match_id,
            )
        )
        prediction = result.scalar_one_or_none()

        if prediction:
            prediction.predicted_score_a = data.home
            prediction.predicted_score_b = data.away
            prediction.updated_at = datetime.now(UTC)
        else:
            prediction = Prediction(
                user_id=user_id,
                match_id=match_id,
                predicted_score_a=data.home,
                predicted_score_b=data.away,
            )
            self.db.add(prediction)

        await self.db.commit()
        await self.db.refresh(prediction)

        reloaded = await self.db.execute(
            select(Prediction)
            .options(
                selectinload(Prediction.match).selectinload(Match.team_a),
                selectinload(Prediction.match).selectinload(Match.team_b),
            )
            .where(Prediction.id == prediction.id)
        )
        return reloaded.scalar_one()

    async def get_user_predictions(self, user_id: int) -> list[Prediction]:
        result = await self.db.execute(
            select(Prediction)
            .options(
                selectinload(Prediction.match).selectinload(Match.team_a),
                selectinload(Prediction.match).selectinload(Match.team_b),
            )
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.match_id)
        )
        return list(result.scalars().all())
