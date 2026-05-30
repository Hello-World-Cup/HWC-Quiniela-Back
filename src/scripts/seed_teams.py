"""Seed script: load 48 World Cup 2026 teams into the database.

Usage:
    uv run python -m src.scripts.seed_teams
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select, text

from src.core.database import AsyncSessionLocal
from src.matches.models import Team

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "wc2026_teams.json"


async def seed_teams() -> None:
    teams_data = json.loads(FIXTURE_PATH.read_text())

    async with AsyncSessionLocal() as db:
        for item in teams_data:
            result = await db.execute(select(Team).where(Team.code == item["code"]))
            team = result.scalar_one_or_none()

            if team:
                team.name = item["name"]
                team.iso_code = item["iso_code"]
                team.group = item["group"]
                team.flag_url = item["flag_url"]
            else:
                db.add(
                    Team(
                        name=item["name"],
                        code=item["code"],
                        iso_code=item["iso_code"],
                        group=item["group"],
                        flag_url=item["flag_url"],
                    )
                )

        await db.commit()
        total = len(teams_data)
        print(f"Seeded {total} teams successfully.")


if __name__ == "__main__":
    asyncio.run(seed_teams())
