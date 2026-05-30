from datetime import date, datetime, timezone

from sqlalchemy import Date, and_, cast, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.matches.models import Match, MatchStatus


class MatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_matches(
        self,
        stage: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        group: str | None = None,
        status: str | None = None,
    ) -> list[Match]:
        query = select(Match).options(
            selectinload(Match.team_a),
            selectinload(Match.team_b),
        )
        conditions = []

        if stage:
            conditions.append(Match.stage == stage)

        if from_date:
            from_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
            conditions.append(Match.start_time >= from_dt)

        if to_date:
            to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59, tzinfo=timezone.utc)
            conditions.append(Match.start_time <= to_dt)

        if group:
            conditions.append(Match.group == group.upper())

        if status:
            # Accept both legacy and new status values
            status_map = {"scheduled": ["scheduled", "pending"], "live": ["live", "in_progress"]}
            mapped = status_map.get(status, [status])
            if len(mapped) > 1:
                conditions.append(Match.status.in_(mapped))
            else:
                conditions.append(Match.status == mapped[0])

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
