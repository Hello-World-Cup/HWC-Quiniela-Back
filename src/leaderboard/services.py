from sqlalchemy import Integer, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.leaderboard.schemas import LeaderboardEntry
from src.predictions.models import Prediction
from src.scoring.constants import POINTS_CORRECT_RESULT, POINTS_EXACT_SCORE


class LeaderboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_leaderboard(self, limit: int = 50) -> list[LeaderboardEntry]:
        total_points = func.coalesce(func.sum(Prediction.points_awarded), 0).label("total_points")
        exact_scores = func.count(
            case((Prediction.points_awarded == POINTS_EXACT_SCORE, 1))
        ).label("exact_scores")
        correct_results = func.count(
            case((Prediction.points_awarded == POINTS_CORRECT_RESULT, 1))
        ).label("correct_results")

        query = (
            select(
                User.id,
                User.full_name,
                User.avatar_url,
                total_points,
                exact_scores,
                correct_results,
            )
            .outerjoin(Prediction, Prediction.user_id == User.id)
            .where(User.is_active == True)  # noqa: E712
            .group_by(User.id, User.full_name, User.avatar_url)
            .order_by(total_points.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        entries = []
        for rank, row in enumerate(rows, start=1):
            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    user_id=str(row.id),
                    display_name=row.full_name,
                    avatar_url=row.avatar_url,
                    total_points=row.total_points,
                    exact_scores=row.exact_scores,
                    correct_results=row.correct_results,
                )
            )
        return entries
