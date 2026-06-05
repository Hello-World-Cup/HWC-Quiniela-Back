"""
Tests para ApiFootballClient.

Mockea httpx.AsyncClient para no realizar llamadas HTTP reales.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.sync.client import ApiFootballClient

API_KEY = "test-key-123"


def _mock_http_client(json_data: dict):
    """Devuelve (context_manager, inner_mock) para patchear httpx.AsyncClient()."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = json_data

    inner = AsyncMock()
    inner.get = AsyncMock(return_value=response)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=inner)
    ctx.__aexit__ = AsyncMock(return_value=None)

    return ctx, inner


# ── get_fixtures_by_ids ────────────────────────────────────────────────────────

async def test_get_fixtures_by_ids_empty_list_makes_no_request():
    client = ApiFootballClient(API_KEY)
    result = await client.get_fixtures_by_ids([])
    assert result == []


async def test_get_fixtures_by_ids_single_batch_joins_ids_with_dash():
    fixture_data = [{"fixture": {"id": 1001}}, {"fixture": {"id": 1002}}]
    ctx, http = _mock_http_client({"response": fixture_data})

    with patch("src.sync.client.httpx.AsyncClient", return_value=ctx):
        client = ApiFootballClient(API_KEY)
        result = await client.get_fixtures_by_ids([1001, 1002])

    assert result == fixture_data
    http.get.assert_called_once()
    params = http.get.call_args.kwargs["params"]
    assert params["ids"] == "1001-1002"


async def test_get_fixtures_by_ids_sends_api_key_header():
    ctx, http = _mock_http_client({"response": []})

    with patch("src.sync.client.httpx.AsyncClient", return_value=ctx):
        client = ApiFootballClient(API_KEY)
        await client.get_fixtures_by_ids([1])

    headers = http.get.call_args.kwargs["headers"]
    assert headers["x-apisports-key"] == API_KEY


async def test_get_fixtures_by_ids_splits_into_batches_of_20():
    """21 IDs → 2 requests: primer batch de 20, segundo de 1."""
    ids = list(range(1, 22))  # 21 IDs

    responses: list[dict] = []

    def make_response(url, **kwargs):
        batch_ids = [int(x) for x in kwargs["params"]["ids"].split("-")]
        r = MagicMock()
        r.raise_for_status = MagicMock()
        r.json.return_value = {"response": [{"fixture": {"id": i}} for i in batch_ids]}
        return r

    inner = AsyncMock()
    inner.get = AsyncMock(side_effect=make_response)
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=inner)
    ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("src.sync.client.httpx.AsyncClient", return_value=ctx):
        client = ApiFootballClient(API_KEY)
        result = await client.get_fixtures_by_ids(ids)

    assert inner.get.call_count == 2
    assert len(result) == 21


# ── get_all_fixtures ───────────────────────────────────────────────────────────

async def test_get_all_fixtures_passes_league_and_season():
    fixture_data = [{"fixture": {"id": 500}}]
    ctx, http = _mock_http_client({"response": fixture_data})

    with patch("src.sync.client.httpx.AsyncClient", return_value=ctx):
        client = ApiFootballClient(API_KEY)
        result = await client.get_all_fixtures()

    assert result == fixture_data
    params = http.get.call_args.kwargs["params"]
    assert params["league"] == 1
    assert params["season"] == 2026


async def test_get_all_fixtures_returns_empty_list_on_empty_response():
    ctx, _ = _mock_http_client({"response": []})

    with patch("src.sync.client.httpx.AsyncClient", return_value=ctx):
        client = ApiFootballClient(API_KEY)
        result = await client.get_all_fixtures()

    assert result == []
