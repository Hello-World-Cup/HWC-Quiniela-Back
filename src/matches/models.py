import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class MatchStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    finished = "finished"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    group: Mapped[str | None] = mapped_column(String(1), nullable=True)
    flag_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.pending, nullable=False
    )
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    group: Mapped[str | None] = mapped_column(String(1), nullable=True)
    round: Mapped[str | None] = mapped_column(String(50), nullable=True)

    team_a: Mapped["Team"] = relationship("Team", foreign_keys=[team_a_id])
    team_b: Mapped["Team"] = relationship("Team", foreign_keys=[team_b_id])
