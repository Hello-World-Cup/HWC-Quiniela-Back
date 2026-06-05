"""
Tests para SyncService.

Usa mocks para la sesión de DB y el ApiFootballClient — no requiere
base de datos real. Se enfoca en la lógica de negocio:
  - sync_pending_matches(): qué pasa con cada status de la API
  - map_fixtures(): mapeo de team+fecha a api_football_id
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.matches.models import MatchStatus
from src.sync.client import ApiFootballClient
from src.sync.service import SyncService


# ── Helpers ───────────────────────────────────────────────────────────────────


@dataclass
class FakeMatch:
    """Sustituto ligero de models.Match para tests."""

    id: int = 1
    api_football_id: int | None = 1001
    status: MatchStatus = MatchStatus.scheduled
    team_a_id: int | None = 1
    team_b_id: int | None = 2
    start_time: datetime = field(
        default_factory=lambda: datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
    )


def scalars_result(objects: list):
    """Mock de db.execute() que soporta .scalars().all()."""
    r = MagicMock()
    r.scalars.return_value.all.return_value = objects
    return r


def row_result(rows: list):
    """Mock de db.execute() que soporta .all() con filas de atributos."""
    r = MagicMock()
    r.all.return_value = rows
    return r


def make_fixture(
    api_id: int = 1001,
    status_short: str = "FT",
    goals_home: int | None = 2,
    goals_away: int | None = 1,
    home_name: str = "Mexico",
    away_name: str = "Argentina",
    date: str = "2026-06-14T18:00:00+00:00",
) -> dict:
    return {
        "fixture": {"id": api_id, "status": {"short": status_short}, "date": date},
        "goals": {"home": goals_home, "away": goals_away},
        "teams": {"home": {"name": home_name}, "away": {"name": away_name}},
    }


# ── sync_pending_matches ───────────────────────────────────────────────────────


async def test_sync_no_pending_matches_returns_all_zeros_without_api_call():
    db = AsyncMock()
    db.execute.return_value = scalars_result([])
    client = AsyncMock(spec=ApiFootballClient)

    result = await SyncService(db, client).sync_pending_matches()

    assert result == {"finalized": 0, "status_updated": 0, "skipped": 0, "errors": 0}
    client.get_fixtures_by_ids.assert_not_called()


async def test_sync_finalizes_ft_match_with_correct_score():
    match = FakeMatch(id=10, api_football_id=1001)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [
        make_fixture(api_id=1001, status_short="FT", goals_home=2, goals_away=1)
    ]

    with patch("src.sync.service.ScoringService") as MockScoring:
        MockScoring.return_value.finalize_match = AsyncMock(return_value=match)
        result = await SyncService(db, client).sync_pending_matches()
        MockScoring.return_value.finalize_match.assert_called_once_with(
            match_id=10, result_a=2, result_b=1
        )

    assert result["finalized"] == 1
    assert result["errors"] == 0


async def test_sync_finalizes_aet_match():
    match = FakeMatch(id=20, api_football_id=2001)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [
        make_fixture(api_id=2001, status_short="AET", goals_home=1, goals_away=1)
    ]

    with patch("src.sync.service.ScoringService") as MockScoring:
        MockScoring.return_value.finalize_match = AsyncMock(return_value=match)
        result = await SyncService(db, client).sync_pending_matches()
        MockScoring.return_value.finalize_match.assert_called_once_with(
            match_id=20, result_a=1, result_b=1
        )

    assert result["finalized"] == 1


async def test_sync_finalizes_pen_match():
    match = FakeMatch(id=30, api_football_id=3001)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [
        make_fixture(api_id=3001, status_short="PEN", goals_home=0, goals_away=0)
    ]

    with patch("src.sync.service.ScoringService") as MockScoring:
        MockScoring.return_value.finalize_match = AsyncMock(return_value=match)
        await SyncService(db, client).sync_pending_matches()
        MockScoring.return_value.finalize_match.assert_called_once()


async def test_sync_updates_status_to_live_for_first_half():
    match = FakeMatch(status=MatchStatus.scheduled)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [make_fixture(status_short="1H")]

    result = await SyncService(db, client).sync_pending_matches()

    assert match.status == MatchStatus.live
    db.commit.assert_called_once()
    assert result["status_updated"] == 1
    assert result["finalized"] == 0


async def test_sync_updates_status_to_live_for_halftime():
    match = FakeMatch(status=MatchStatus.scheduled)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [make_fixture(status_short="HT")]

    result = await SyncService(db, client).sync_pending_matches()

    assert match.status == MatchStatus.live
    assert result["status_updated"] == 1


async def test_sync_updates_status_to_postponed():
    match = FakeMatch(status=MatchStatus.scheduled)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [make_fixture(status_short="PST")]

    result = await SyncService(db, client).sync_pending_matches()

    assert match.status == MatchStatus.postponed
    db.commit.assert_called_once()
    assert result["status_updated"] == 1


async def test_sync_skips_ft_match_when_goals_are_none():
    """Si la API devuelve FT pero sin goles todavía, no se finaliza."""
    match = FakeMatch()
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [
        make_fixture(status_short="FT", goals_home=None, goals_away=None)
    ]

    with patch("src.sync.service.ScoringService") as MockScoring:
        result = await SyncService(db, client).sync_pending_matches()
        MockScoring.return_value.finalize_match.assert_not_called()

    assert result["skipped"] == 1
    assert result["finalized"] == 0


async def test_sync_skips_ns_status():
    """NS (Not Started) no debería cambiar nada."""
    match = FakeMatch(status=MatchStatus.scheduled)
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [make_fixture(status_short="NS")]

    with patch("src.sync.service.ScoringService") as MockScoring:
        result = await SyncService(db, client).sync_pending_matches()
        MockScoring.return_value.finalize_match.assert_not_called()

    assert result["skipped"] == 1
    assert match.status == MatchStatus.scheduled


async def test_sync_counts_error_when_finalize_raises():
    """Un error en ScoringService se captura y cuenta en 'errors', no propaga."""
    match = FakeMatch()
    db = AsyncMock()
    db.execute.return_value = scalars_result([match])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [make_fixture(status_short="FT")]

    with patch("src.sync.service.ScoringService") as MockScoring:
        MockScoring.return_value.finalize_match = AsyncMock(
            side_effect=Exception("DB connection lost")
        )
        result = await SyncService(db, client).sync_pending_matches()

    assert result["errors"] == 1
    assert result["finalized"] == 0


async def test_sync_handles_multiple_matches_independently():
    """Errores en un partido no impiden procesar los siguientes."""
    match_ok = FakeMatch(id=1, api_football_id=1001)
    match_err = FakeMatch(id=2, api_football_id=1002)
    match_live = FakeMatch(id=3, api_football_id=1003, status=MatchStatus.scheduled)

    db = AsyncMock()
    db.execute.return_value = scalars_result([match_ok, match_err, match_live])
    client = AsyncMock(spec=ApiFootballClient)
    client.get_fixtures_by_ids.return_value = [
        make_fixture(api_id=1001, status_short="FT", goals_home=1, goals_away=0),
        make_fixture(api_id=1002, status_short="FT", goals_home=2, goals_away=1),
        make_fixture(api_id=1003, status_short="2H"),
    ]

    call_count = 0

    async def finalize_side_effect(match_id, result_a, result_b):
        nonlocal call_count
        call_count += 1
        if match_id == 2:
            raise Exception("scoring failed")

    with patch("src.sync.service.ScoringService") as MockScoring:
        MockScoring.return_value.finalize_match = AsyncMock(
            side_effect=finalize_side_effect
        )
        result = await SyncService(db, client).sync_pending_matches()

    assert result["finalized"] == 1
    assert result["errors"] == 1
    assert result["status_updated"] == 1
    assert match_live.status == MatchStatus.live


# ── map_fixtures ──────────────────────────────────────────────────────────────


async def test_map_fixtures_matches_by_team_codes_and_date():
    team_rows = [
        SimpleNamespace(name="Mexico", code="MEX"),
        SimpleNamespace(name="Argentina", code="ARG"),
    ]
    match = FakeMatch(id=5, api_football_id=None, team_a_id=1, team_b_id=2)
    id_rows = [SimpleNamespace(id=1, code="MEX"), SimpleNamespace(id=2, code="ARG")]

    db = AsyncMock()
    db.execute.side_effect = [
        row_result(team_rows),
        scalars_result([match]),
        row_result(id_rows),
    ]
    client = AsyncMock(spec=ApiFootballClient)
    client.get_all_fixtures.return_value = [
        make_fixture(api_id=9999, home_name="Mexico", away_name="Argentina")
    ]

    result = await SyncService(db, client).map_fixtures()

    assert match.api_football_id == 9999
    assert result["mapped"] == 1
    assert result["not_found_in_api"] == 0
    db.commit.assert_called_once()


async def test_map_fixtures_tries_inverted_home_away():
    """La API puede tener home/away invertido respecto a team_a/team_b."""
    team_rows = [
        SimpleNamespace(name="Brazil", code="BRA"),
        SimpleNamespace(name="Germany", code="GER"),
    ]
    # En DB: team_a=BRA, team_b=GER
    # En API: home=Germany, away=Brazil (invertido)
    match = FakeMatch(id=6, api_football_id=None, team_a_id=1, team_b_id=2)
    id_rows = [SimpleNamespace(id=1, code="BRA"), SimpleNamespace(id=2, code="GER")]

    db = AsyncMock()
    db.execute.side_effect = [
        row_result(team_rows),
        scalars_result([match]),
        row_result(id_rows),
    ]
    client = AsyncMock(spec=ApiFootballClient)
    client.get_all_fixtures.return_value = [
        make_fixture(api_id=8888, home_name="Germany", away_name="Brazil")
    ]

    result = await SyncService(db, client).map_fixtures()

    assert match.api_football_id == 8888
    assert result["mapped"] == 1


async def test_map_fixtures_normalizes_team_name_casing():
    """Nombres en minúsculas/mayúsculas mixtas deben igualarse."""
    team_rows = [
        SimpleNamespace(name="Côte d'Ivoire", code="CIV"),
        SimpleNamespace(name="Morocco", code="MAR"),
    ]
    match = FakeMatch(id=7, api_football_id=None, team_a_id=1, team_b_id=2)
    id_rows = [SimpleNamespace(id=1, code="CIV"), SimpleNamespace(id=2, code="MAR")]

    db = AsyncMock()
    db.execute.side_effect = [
        row_result(team_rows),
        scalars_result([match]),
        row_result(id_rows),
    ]
    client = AsyncMock(spec=ApiFootballClient)
    # API devuelve el nombre en mayúsculas
    client.get_all_fixtures.return_value = [
        make_fixture(api_id=7777, home_name="CÔTE D'IVOIRE", away_name="MOROCCO")
    ]

    result = await SyncService(db, client).map_fixtures()

    assert match.api_football_id == 7777
    assert result["mapped"] == 1


async def test_map_fixtures_logs_not_found_when_api_has_no_match():
    team_rows = [SimpleNamespace(name="France", code="FRA")]
    match = FakeMatch(id=8, api_football_id=None, team_a_id=1, team_b_id=2)
    id_rows = [SimpleNamespace(id=1, code="FRA"), SimpleNamespace(id=2, code="ESP")]

    db = AsyncMock()
    db.execute.side_effect = [
        row_result(team_rows),
        scalars_result([match]),
        row_result(id_rows),
    ]
    client = AsyncMock(spec=ApiFootballClient)
    client.get_all_fixtures.return_value = []  # API no devuelve nada

    result = await SyncService(db, client).map_fixtures()

    assert match.api_football_id is None
    assert result["not_found_in_api"] == 1
    assert result["mapped"] == 0


async def test_map_fixtures_no_pending_matches_skips_commit():
    db = AsyncMock()
    db.execute.side_effect = [
        row_result([]),         # teams
        scalars_result([]),     # matches
        row_result([]),         # id→code
    ]
    client = AsyncMock(spec=ApiFootballClient)
    client.get_all_fixtures.return_value = []

    result = await SyncService(db, client).map_fixtures()

    assert result == {"mapped": 0, "not_found_in_api": 0}
    db.commit.assert_called_once()  # siempre hace commit al final
