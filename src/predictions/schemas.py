from datetime import datetime

from pydantic import BaseModel, Field

from src.matches.schemas import MatchResponse


class PredictionCreate(BaseModel):
    match_id: int
    predicted_score_a: int = Field(ge=0)
    predicted_score_b: int = Field(ge=0)


class PredictionResponse(BaseModel):
    id: int
    match_id: int
    match: MatchResponse
    predicted_score_a: int
    predicted_score_b: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
