from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.matches.models import Match, MatchStatus
from src.predictions.models import Prediction
from src.scoring.engine import score_prediction


class ScoringService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def finalize_match(
        self, match_id: int, result_a: int, result_b: int
    ) -> Match:
        result = await self.db.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Partido no encontrado")

        match.result_a = result_a
        match.result_b = result_b
        match.status = MatchStatus.finished

        preds = await self.db.execute(
            select(Prediction).where(Prediction.match_id == match_id)
        )
        for prediction in preds.scalars().all():
            prediction.points_awarded = score_prediction(
                result_a, result_b,
                prediction.predicted_score_a,
                prediction.predicted_score_b,
            )

        await self.db.commit()
        await self.db.refresh(match)
        return match
