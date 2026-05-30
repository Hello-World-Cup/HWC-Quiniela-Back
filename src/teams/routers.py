from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.teams.schemas import TeamResponse
from src.teams.services import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "",
    response_model=list[TeamResponse],
    response_model_by_alias=True,
    summary="Listar todos los equipos",
    response_description="Lista de 48 equipos ordenados por grupo y nombre",
)
async def list_teams(db: AsyncSession = Depends(get_db)) -> list[TeamResponse]:
    """
    Devuelve los 48 equipos participantes del Mundial 2026.

    El campo `id` es el código **ISO 3166-1 alpha-2** del país (ej: `mx`, `ar`, `gb-eng`).
    Úsalo para identificar al equipo en otras peticiones como predicciones o filtros de partidos.
    """
    teams = await TeamService(db).get_all_teams()
    return [TeamResponse.from_orm_team(t) for t in teams]


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    response_model_by_alias=True,
    summary="Obtener equipo por ISO code",
    response_description="Detalle del equipo",
    responses={404: {"description": "Equipo no encontrado"}},
)
async def get_team(team_id: str, db: AsyncSession = Depends(get_db)) -> TeamResponse:
    """
    Retorna la información de un equipo por su código **ISO 3166-1 alpha-2**.

    **Ejemplos de IDs válidos:**
    - `mx` — México
    - `ar` — Argentina
    - `gb-eng` — Inglaterra
    - `gb-sct` — Escocia
    - `us` — Estados Unidos
    """
    team = await TeamService(db).get_team_by_iso_code(team_id)
    return TeamResponse.from_orm_team(team)
