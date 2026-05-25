from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.matches.models import MatchStatus
from src.matches.schemas import MatchResponse
from src.matches.services import MatchService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    filter_date: date | None = Query(None, alias="date", description="Filter by date (YYYY-MM-DD)"),
    group: str | None = Query(None, description="Filter by group letter (A-H)"),
    status: MatchStatus | None = Query(None, description="Filter by match status"),
    db: AsyncSession = Depends(get_db),
) -> list:
    return await MatchService(db).get_matches(
        filter_date=filter_date, group=group, status=status
    )
