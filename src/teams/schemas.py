from pydantic import Field

from src.core.schemas import BaseSchema


class TeamResponse(BaseSchema):
    id: str = Field(
        description="Código ISO 3166-1 alpha-2 del país. Úsalo como identificador en otras peticiones.",
        examples=["mx", "ar", "gb-eng"],
    )
    name: str = Field(description="Nombre completo del país", examples=["Mexico", "Argentina", "England"])
    code: str = Field(description="Código FIFA de 3 letras", examples=["MEX", "ARG", "ENG"])
    flag_url: str | None = Field(
        description="URL a la imagen de la bandera en formato SVG",
        examples=["https://flagcdn.com/mx.svg"],
    )
    group: str | None = Field(
        description="Grupo del equipo (A–L). Null si no aplica.",
        examples=["A", "G"],
    )

    @classmethod
    def from_orm_team(cls, team: object) -> "TeamResponse":
        return cls(
            id=getattr(team, "iso_code") or str(getattr(team, "id")),
            name=getattr(team, "name"),
            code=getattr(team, "code"),
            flag_url=getattr(team, "flag_url"),
            group=getattr(team, "group"),
        )
