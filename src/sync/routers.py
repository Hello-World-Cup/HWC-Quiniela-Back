from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.core.config import settings
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.schemas import BaseSchema
from src.sync.client import ApiFootballClient
from src.sync.service import SyncService

router = APIRouter(prefix="/admin/sync", tags=["admin"])


class SyncResult(BaseSchema):
    finalized: int
    status_updated: int
    skipped: int
    errors: int


class MappingResult(BaseSchema):
    mapped: int
    not_found_in_api: int


@router.post(
    "/run",
    response_model=SyncResult,
    response_model_by_alias=True,
    summary="Disparar sincronización manual con API-Football",
)
async def run_sync_now(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncResult:
    """
    Ejecuta inmediatamente la sincronización de resultados de todos los partidos
    pendientes. Útil para forzar actualización sin esperar el job diario.
    """
    client = ApiFootballClient(settings.api_football_key)
    result = await SyncService(db, client).sync_pending_matches()
    return SyncResult(**result)


@router.post(
    "/map-fixtures",
    response_model=MappingResult,
    response_model_by_alias=True,
    summary="Mapear fixtures de API-Football a partidos locales (una sola vez)",
)
async def map_fixtures(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MappingResult:
    """
    Descarga todos los fixtures del Mundial 2026 desde API-Football y los empareja
    con los partidos de la base de datos por código de equipo + fecha.
    Almacena `api_football_id` en cada partido. Idempotente: omite los ya mapeados.

    Solo necesita ejecutarse una vez antes de que inicie el torneo.
    """
    client = ApiFootballClient(settings.api_football_key)
    result = await SyncService(db, client).map_fixtures()
    return MappingResult(**result)
