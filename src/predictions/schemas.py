from datetime import datetime

from pydantic import Field

from src.core.schemas import BaseSchema
from src.matches.schemas import MatchResponse


class PredictionCreate(BaseSchema):
    match_id: str = Field(
        alias="matchId",
        description="ID del partido a pronosticar",
        examples=["1"],
    )
    home: int = Field(
        ge=0,
        description="Goles pronosticados para el equipo local",
        examples=[2],
    )
    away: int = Field(
        ge=0,
        description="Goles pronosticados para el equipo visitante",
        examples=[1],
    )


class ScoreResponse(BaseSchema):
    home: int = Field(description="Goles del equipo local", examples=[2])
    away: int = Field(description="Goles del equipo visitante", examples=[1])


class PredictionResponse(BaseSchema):
    id: str = Field(description="ID del pronóstico", examples=["42"])
    user_id: str = Field(description="ID del usuario que realizó el pronóstico", examples=["7"])
    match_id: str = Field(description="ID del partido pronosticado", examples=["1"])
    predicted_score: ScoreResponse = Field(description="Marcador pronosticado")
    points_awarded: int | None = Field(
        description="Puntos obtenidos. Null hasta que el partido sea finalizado por el admin.",
        examples=[3, 1, 0, None],
    )
    submitted_at: datetime = Field(description="Fecha y hora en que se realizó el pronóstico (UTC)")
    match: MatchResponse | None = Field(
        default=None,
        description="Detalle del partido. Incluido cuando se consulta via /predictions/me o /users/{id}/predictions.",
    )

    @classmethod
    def from_orm_prediction(cls, prediction: object) -> "PredictionResponse":
        match = getattr(prediction, "match", None)
        return cls(
            id=str(getattr(prediction, "id")),
            user_id=str(getattr(prediction, "user_id")),
            match_id=str(getattr(prediction, "match_id")),
            predicted_score=ScoreResponse(
                home=getattr(prediction, "predicted_score_a"),
                away=getattr(prediction, "predicted_score_b"),
            ),
            points_awarded=getattr(prediction, "points_awarded", None),
            submitted_at=getattr(prediction, "created_at"),
            match=MatchResponse.from_orm_match(match) if match else None,
        )
