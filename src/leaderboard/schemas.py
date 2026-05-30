from pydantic import Field

from src.core.schemas import BaseSchema


class LeaderboardEntry(BaseSchema):
    rank: int = Field(description="Posición en la tabla (1 = primero)", examples=[1])
    user_id: str = Field(description="ID del usuario", examples=["7"])
    display_name: str = Field(description="Nombre completo del participante", examples=["Juan García"])
    avatar_url: str | None = Field(
        description="URL de la foto de perfil de Google",
        examples=["https://lh3.googleusercontent.com/a/..."],
    )
    total_points: int = Field(description="Puntos totales acumulados", examples=[27])
    exact_scores: int = Field(description="Cantidad de pronósticos con marcador exacto (3 pts c/u)", examples=[9])
    correct_results: int = Field(
        description="Cantidad de pronósticos con resultado correcto pero marcador incorrecto (1 pt c/u)",
        examples=[0],
    )
