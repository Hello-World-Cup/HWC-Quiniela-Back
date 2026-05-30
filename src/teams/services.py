from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.matches.models import Team


class TeamService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_teams(self) -> list[Team]:
        result = await self.db.execute(select(Team).order_by(Team.group, Team.name))
        return list(result.scalars().all())

    async def get_team_by_iso_code(self, iso_code: str) -> Team:
        result = await self.db.execute(select(Team).where(Team.iso_code == iso_code))
        team = result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Equipo no encontrado")
        return team
