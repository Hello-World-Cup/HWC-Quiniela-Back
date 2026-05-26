from datetime import datetime

from pydantic import BaseModel

from src.matches.models import MatchStatus


class TeamResponse(BaseModel):
    id: int
    name: str
    code: str
    group: str | None
    flag_url: str | None

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    id: int
    team_a: TeamResponse
    team_b: TeamResponse
    start_time: datetime
    prediction_deadline: datetime | None
    result_a: int | None
    result_b: int | None
    status: MatchStatus
    venue: str | None
    group: str | None
    round: str | None

    model_config = {"from_attributes": True}
