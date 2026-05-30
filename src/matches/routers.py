from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.matches.schemas import MatchResponse
from src.matches.services import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get(
    "",
    response_model=list[MatchResponse],
    response_model_by_alias=True,
    summary="Listar partidos",
    response_description="Lista de partidos ordenados por fecha de inicio",
)
async def list_matches(
    stage: str | None = Query(
        None,
        description="Fase del torneo",
        examples=["group", "round-of-16", "quarter-final", "semi-final", "final"],
    ),
    from_date: date | None = Query(
        None,
        alias="from",
        description="Fecha de inicio del rango (YYYY-MM-DD)",
        examples=["2026-06-11"],
    ),
    to_date: date | None = Query(
        None,
        alias="to",
        description="Fecha de fin del rango (YYYY-MM-DD)",
        examples=["2026-06-30"],
    ),
    group: str | None = Query(
        None,
        description="Letra del grupo (A–L)",
        examples=["A", "B", "G"],
    ),
    status: str | None = Query(
        None,
        description="Estado del partido",
        examples=["scheduled", "live", "finished", "postponed"],
    ),
    db: AsyncSession = Depends(get_db),
) -> list[MatchResponse]:
    """
    Devuelve todos los partidos del Mundial 2026, con soporte para múltiples filtros combinables.

    **Ejemplos de uso:**
    - `/matches?stage=group` — todos los partidos de fase de grupos
    - `/matches?from=2026-06-11&to=2026-06-30` — partidos de junio
    - `/matches?group=A` — partidos del Grupo A
    - `/matches?status=live` — partidos en curso ahora mismo
    """
    matches = await MatchService(db).get_matches(
        stage=stage,
        from_date=from_date,
        to_date=to_date,
        group=group,
        status=status,
    )
    return [MatchResponse.from_orm_match(m) for m in matches]


@router.get(
    "/{match_id}",
    response_model=MatchResponse,
    response_model_by_alias=True,
    summary="Obtener partido por ID",
    response_description="Detalle completo del partido incluyendo equipos y marcador",
    responses={404: {"description": "Partido no encontrado"}},
)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)) -> MatchResponse:
    """
    Retorna el detalle de un partido específico, incluyendo:
    - Información de ambos equipos (`homeTeam` / `awayTeam`)
    - Fecha y hora de inicio (`kickoff`)
    - Estado actual (`scheduled`, `live`, `finished`, `postponed`)
    - Marcador (`score`) si el partido ya terminó
    - Fase del torneo (`stage`)
    """
    match = await MatchService(db).get_match_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return MatchResponse.from_orm_match(match)
