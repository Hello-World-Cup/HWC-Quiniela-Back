import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class MatchStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    finished = "finished"
    scheduled = "scheduled"
    live = "live"
    postponed = "postponed"


class MatchStage(str, enum.Enum):
    group = "group"
    round_of_32 = "round-of-32"
    round_of_16 = "round-of-16"
    quarter_final = "quarter-final"
    semi_final = "semi-final"
    third_place = "third-place"
    final = "final"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    iso_code: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True, index=True)
    group: Mapped[str | None] = mapped_column(String(2), nullable=True)
    flag_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_a_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    team_b_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prediction_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus), default=MatchStatus.scheduled, nullable=False
    )
    venue: Mapped[str | None] = mapped_column(String(200), nullable=True)
    group: Mapped[str | None] = mapped_column(String(2), nullable=True)
    round: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    match_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fifa_number: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)

    team_a: Mapped["Team | None"] = relationship("Team", foreign_keys=[team_a_id])
    team_b: Mapped["Team | None"] = relationship("Team", foreign_keys=[team_b_id])
