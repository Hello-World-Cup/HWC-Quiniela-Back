from datetime import date

from sqlalchemy import Date, and_, cast, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.matches.models import Match, MatchStatus


class MatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_matches(
        self,
        filter_date: date | None = None,
        group: str | None = None,
        status: MatchStatus | None = None,
    ) -> list[Match]:
        query = select(Match).options(
            selectinload(Match.team_a),
            selectinload(Match.team_b),
        )
        conditions = []

        if filter_date:
            conditions.append(cast(Match.start_time, Date) == filter_date)

        if group:
            conditions.append(Match.group == group.upper())

        if status:
            conditions.append(Match.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Match.start_time)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_match_by_id(self, match_id: int) -> Match | None:
        result = await self.db.execute(
            select(Match)
            .options(selectinload(Match.team_a), selectinload(Match.team_b))
            .where(Match.id == match_id)
        )
        return result.scalar_one_or_none()
