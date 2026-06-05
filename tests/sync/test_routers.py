"""
Tests de humo para los endpoints de sincronización.

Verifica que la capa HTTP (auth, respuesta JSON, camelCase) funcione
correctamente sin ejecutar lógica real de negocio.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.auth.models import User
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.main import app

BASE_URL = "http://test"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def disable_scheduler():
    """Evita que APScheduler arranque/pare durante los tests de HTTP."""
    with patch("src.main.start_scheduler"), patch("src.main.stop_scheduler"):
        yield


@pytest.fixture
def fake_user():
    user = User()
    user.id = 1
    user.email = "admin@test.com"
    user.full_name = "Admin Test"
    user.is_active = True
    return user


@pytest.fixture
def authenticated(fake_user):
    """Override get_current_user para no requerir JWT real en tests."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_db():
    """Override get_db con una sesión mock."""
    db = AsyncMock()

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


# ── POST /admin/sync/run ───────────────────────────────────────────────────────


async def test_run_sync_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        r = await client.post("/admin/sync/run")
    assert r.status_code == 401


async def test_run_sync_returns_200_with_sync_result(authenticated, mock_db):
    sync_result = {"finalized": 3, "status_updated": 1, "skipped": 0, "errors": 0}

    with patch("src.sync.routers.SyncService") as MockService:
        MockService.return_value.sync_pending_matches = AsyncMock(return_value=sync_result)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.post("/admin/sync/run")

    assert r.status_code == 200
    data = r.json()
    assert data["finalized"] == 3
    assert data["statusUpdated"] == 1  # camelCase por BaseSchema
    assert data["skipped"] == 0
    assert data["errors"] == 0


async def test_run_sync_response_is_camel_case(authenticated, mock_db):
    sync_result = {"finalized": 0, "status_updated": 2, "skipped": 1, "errors": 0}

    with patch("src.sync.routers.SyncService") as MockService:
        MockService.return_value.sync_pending_matches = AsyncMock(return_value=sync_result)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.post("/admin/sync/run")

    keys = r.json().keys()
    assert "statusUpdated" in keys
    assert "status_updated" not in keys


# ── POST /admin/sync/map-fixtures ─────────────────────────────────────────────


async def test_map_fixtures_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        r = await client.post("/admin/sync/map-fixtures")
    assert r.status_code == 401


async def test_map_fixtures_returns_200_with_mapping_result(authenticated, mock_db):
    mapping_result = {"mapped": 90, "not_found_in_api": 14}

    with patch("src.sync.routers.SyncService") as MockService:
        MockService.return_value.map_fixtures = AsyncMock(return_value=mapping_result)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.post("/admin/sync/map-fixtures")

    assert r.status_code == 200
    data = r.json()
    assert data["mapped"] == 90
    assert data["notFoundInApi"] == 14  # camelCase


async def test_map_fixtures_response_is_camel_case(authenticated, mock_db):
    mapping_result = {"mapped": 5, "not_found_in_api": 2}

    with patch("src.sync.routers.SyncService") as MockService:
        MockService.return_value.map_fixtures = AsyncMock(return_value=mapping_result)
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            r = await client.post("/admin/sync/map-fixtures")

    keys = r.json().keys()
    assert "notFoundInApi" in keys
    assert "not_found_in_api" not in keys
