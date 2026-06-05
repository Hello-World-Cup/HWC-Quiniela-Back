import logging
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.matches.models import Match, MatchStatus, Team
from src.scoring.service import ScoringService
from src.sync.client import ApiFootballClient

logger = logging.getLogger(__name__)

LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P"}
TERMINAL_STATUSES = {"FT", "AET", "PEN"}
POSTPONED_STATUSES = {"PST", "CANC", "SUSP"}


class SyncService:
    def __init__(self, db: AsyncSession, client: ApiFootballClient) -> None:
        self.db = db
        self.client = client

    async def sync_pending_matches(self) -> dict:
        """
        Fetch results for all unfinished mapped matches and finalize those that ended.
        Idempotent: already-finished matches are excluded by the DB query.
        """
        result = await self.db.execute(
            select(Match).where(
                Match.api_football_id.isnot(None),
                Match.status.notin_([MatchStatus.finished, MatchStatus.postponed]),
            )
        )
        pending = result.scalars().all()

        if not pending:
            logger.info("No hay partidos pendientes para sincronizar")
            return {"finalized": 0, "status_updated": 0, "skipped": 0, "errors": 0}

        api_ids = [m.api_football_id for m in pending]
        id_to_match = {m.api_football_id: m for m in pending}

        fixtures = await self.client.get_fixtures_by_ids(api_ids)

        finalized = status_updated = skipped = errors = 0

        for fixture in fixtures:
            api_id = fixture["fixture"]["id"]
            api_status = fixture["fixture"]["status"]["short"]
            match = id_to_match.get(api_id)

            if match is None:
                skipped += 1
                continue

            try:
                if api_status in TERMINAL_STATUSES:
                    goals_home = fixture["goals"]["home"]
                    goals_away = fixture["goals"]["away"]
                    if goals_home is None or goals_away is None:
                        logger.warning(
                            "Fixture %d tiene status %s pero sin goles, omitiendo",
                            api_id, api_status,
                        )
                        skipped += 1
                        continue
                    await ScoringService(self.db).finalize_match(
                        match_id=match.id,
                        result_a=int(goals_home),
                        result_b=int(goals_away),
                    )
                    finalized += 1

                elif api_status in LIVE_STATUSES:
                    match.status = MatchStatus.live
                    await self.db.commit()
                    status_updated += 1

                elif api_status in POSTPONED_STATUSES:
                    match.status = MatchStatus.postponed
                    await self.db.commit()
                    status_updated += 1

                else:
                    logger.debug("Status '%s' del fixture %d no requiere acción", api_status, api_id)
                    skipped += 1

            except Exception:
                logger.exception("Error procesando fixture %d (match_id=%d)", api_id, match.id)
                errors += 1

        summary = {
            "finalized": finalized,
            "status_updated": status_updated,
            "skipped": skipped,
            "errors": errors,
        }
        logger.info("Sync completado: %s", summary)
        return summary

    async def map_fixtures(self) -> dict:
        """
        One-time mapping: fetch all WC2026 fixtures and store api_football_id on each Match.
        Safe to re-run — skips already-mapped rows.
        """
        all_fixtures = await self.client.get_all_fixtures()

        # Build team name → code reverse map
        teams_result = await self.db.execute(select(Team.name, Team.code))
        name_to_code: dict[str, str] = {
            row.name.lower(): row.code for row in teams_result.all()
        }

        # Build lookup: (home_code, away_code, "YYYY-MM-DD") → api_fixture_id
        api_lookup: dict[tuple[str, str, str], int] = {}
        for fixture in all_fixtures:
            home_name = fixture["teams"]["home"]["name"].lower()
            away_name = fixture["teams"]["away"]["name"].lower()
            home_code = name_to_code.get(home_name)
            away_code = name_to_code.get(away_name)
            if not home_code or not away_code:
                continue
            fixture_date = fixture["fixture"]["date"][:10]
            api_lookup[(home_code, away_code, fixture_date)] = fixture["fixture"]["id"]

        # Load unresolved matches with both teams assigned
        matches_result = await self.db.execute(
            select(Match).where(
                Match.api_football_id.is_(None),
                Match.team_a_id.isnot(None),
                Match.team_b_id.isnot(None),
            )
        )
        matches = matches_result.scalars().all()

        # Build team id → code map
        id_result = await self.db.execute(select(Team.id, Team.code))
        id_to_code: dict[int, str] = {row.id: row.code for row in id_result.all()}

        mapped = not_found = 0

        for match in matches:
            match_date = match.start_time.astimezone(UTC).date().isoformat()
            team_a_code = id_to_code.get(match.team_a_id)
            team_b_code = id_to_code.get(match.team_b_id)

            if not team_a_code or not team_b_code:
                not_found += 1
                continue

            api_id = api_lookup.get((team_a_code, team_b_code, match_date))
            if api_id is None:
                api_id = api_lookup.get((team_b_code, team_a_code, match_date))

            if api_id is None:
                logger.warning(
                    "No se encontró fixture en API para match id=%d (%s vs %s el %s)",
                    match.id, team_a_code, team_b_code, match_date,
                )
                not_found += 1
                continue

            match.api_football_id = api_id
            mapped += 1

        await self.db.commit()

        summary = {"mapped": mapped, "not_found_in_api": not_found}
        logger.info("Mapeo de fixtures completo: %s", summary)
        return summary
