from datetime import datetime

from pydantic import Field

from src.core.schemas import BaseSchema
from src.matches.models import Match
from src.teams.schemas import TeamResponse


class ScoreResponse(BaseSchema):
    home: int = Field(description="Goles del equipo local", examples=[2])
    away: int = Field(description="Goles del equipo visitante", examples=[1])


class MatchResponse(BaseSchema):
    id: str = Field(description="ID del partido", examples=["1"])
    stage: str | None = Field(
        description="Fase del torneo",
        examples=["group", "round-of-16", "quarter-final", "semi-final", "final"],
    )
    group: str | None = Field(description="Letra del grupo (A–L). Null en eliminatorias.", examples=["A"])
    kickoff: datetime = Field(description="Fecha y hora de inicio en UTC")
    venue: str | None = Field(description="Estadio donde se juega el partido", examples=["MetLife Stadium, New York"])
    status: str = Field(
        description="Estado del partido",
        examples=["scheduled", "live", "finished", "postponed"],
    )
    home_team: TeamResponse | None = Field(description="Equipo local. Null en eliminatorias sin equipos confirmados.")
    away_team: TeamResponse | None = Field(description="Equipo visitante. Null en eliminatorias sin equipos confirmados.")
    score: ScoreResponse | None = Field(description="Marcador final. Null si el partido no ha terminado.")
    prediction_deadline: datetime | None = Field(
        description="Cierre de pronósticos. Si es null, usa la hora de inicio como cierre."
    )
    match_label: str | None = Field(
        description="Etiqueta para partidos de eliminatoria sin equipos definidos aún.",
        examples=["Winner Group A vs Runner-up Group B"],
    )
    fifa_number: int | None = Field(
        default=None,
        description="Número oficial FIFA del partido (73–104 para eliminatoria). Usado por el frontend para mapear predicciones.",
        examples=[73, 89, 97],
    )

    @classmethod
    def from_orm_match(cls, match: Match) -> "MatchResponse":
        score = None
        if match.result_a is not None and match.result_b is not None:
            score = ScoreResponse(home=match.result_a, away=match.result_b)

        status_map = {
            "pending": "scheduled",
            "in_progress": "live",
            "finished": "finished",
            "scheduled": "scheduled",
            "live": "live",
            "postponed": "postponed",
        }
        status = status_map.get(
            match.status.value if hasattr(match.status, "value") else str(match.status),
            "scheduled",
        )

        return cls(
            id=str(match.id),
            stage=match.stage,
            group=match.group,
            kickoff=match.start_time,
            venue=match.venue,
            status=status,
            home_team=TeamResponse.from_orm_team(match.team_a) if match.team_a else None,
            away_team=TeamResponse.from_orm_team(match.team_b) if match.team_b else None,
            score=score,
            prediction_deadline=match.prediction_deadline,
            match_label=match.match_label,
            fifa_number=match.fifa_number,
        )
