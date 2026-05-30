"""Seed script: load World Cup 2026 match schedule into the database.

Run seed_teams.py first so team codes exist.

Usage:
    uv run python -m src.scripts.seed_matches
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.matches.models import Match, MatchStatus, Team

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "wc2026_matches.json"


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


async def seed_matches() -> None:
    data = json.loads(FIXTURE_PATH.read_text())

    async with AsyncSessionLocal() as db:
        # Pre-load team code → id map
        result = await db.execute(select(Team.id, Team.code))
        code_to_id: dict[str, int] = {row.code: row.id for row in result.all()}

        created = 0

        for item in data.get("group_stage", []):
            team_a_id = code_to_id.get(item["team_a"])
            team_b_id = code_to_id.get(item["team_b"])
            if not team_a_id or not team_b_id:
                print(f"WARNING: team code not found for match {item['team_a']} vs {item['team_b']}, skipping")
                continue

            match = Match(
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                start_time=parse_dt(item["start_time"]),
                status=MatchStatus.scheduled,
                venue=item.get("venue"),
                group=item.get("group"),
                stage=item.get("stage"),
                round=item.get("stage", "").replace("-", " ").title(),
            )
            db.add(match)
            created += 1

        for item in data.get("knockout_stage", []):
            match = Match(
                team_a_id=None,
                team_b_id=None,
                start_time=parse_dt(item["start_time"]),
                status=MatchStatus.scheduled,
                venue=item.get("venue"),
                stage=item.get("stage"),
                match_label=item.get("match_label"),
                fifa_number=item.get("fifa_number"),
                round=item.get("stage", "").replace("-", " ").title(),
            )
            db.add(match)
            created += 1

        await db.commit()
        print(f"Seeded {created} matches successfully.")


if __name__ == "__main__":
    asyncio.run(seed_matches())
