"""additive model changes for frontend alignment

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add iso_code to teams (nullable initially; 0003 sets NOT NULL after seed)
    op.add_column("teams", sa.Column("iso_code", sa.String(10), nullable=True))
    op.create_index("ix_teams_iso_code", "teams", ["iso_code"], unique=True)

    # Extend team group to support A-L (World Cup 2026 has 12 groups)
    op.alter_column("teams", "group", existing_type=sa.String(1), type_=sa.String(2))

    # Add avatar_url to users
    op.add_column("users", sa.Column("avatar_url", sa.String(500), nullable=True))

    # Add points_awarded to predictions
    op.add_column("predictions", sa.Column("points_awarded", sa.Integer, nullable=True))

    # Add stage and match_label to matches
    op.add_column("matches", sa.Column("stage", sa.String(20), nullable=True))
    op.add_column("matches", sa.Column("match_label", sa.String(100), nullable=True))

    # Make team_a_id and team_b_id nullable for knockout placeholder matches
    op.alter_column("matches", "team_a_id", existing_type=sa.Integer, nullable=True)
    op.alter_column("matches", "team_b_id", existing_type=sa.Integer, nullable=True)

    # Extend match group to support A-L
    op.alter_column("matches", "group", existing_type=sa.String(1), type_=sa.String(2))

    # ALTER TYPE ADD VALUE must run outside a transaction in PostgreSQL.
    # We commit the current Alembic transaction, run the ALTERs, then re-open.
    bind = op.get_bind()
    bind.execute(sa.text("COMMIT"))
    for value in ("scheduled", "live", "postponed"):
        bind.execute(sa.text(f"ALTER TYPE matchstatus ADD VALUE IF NOT EXISTS '{value}'"))
    bind.execute(sa.text("BEGIN"))


def downgrade() -> None:
    op.drop_index("ix_teams_iso_code", table_name="teams")
    op.drop_column("teams", "iso_code")
    op.alter_column("teams", "group", existing_type=sa.String(2), type_=sa.String(1))
    op.drop_column("users", "avatar_url")
    op.drop_column("predictions", "points_awarded")
    op.drop_column("matches", "stage")
    op.drop_column("matches", "match_label")
    op.alter_column("matches", "team_a_id", existing_type=sa.Integer, nullable=False)
    op.alter_column("matches", "team_b_id", existing_type=sa.Integer, nullable=False)
    op.alter_column("matches", "group", existing_type=sa.String(2), type_=sa.String(1))
    # Note: PostgreSQL does not support removing enum values; downgrade leaves them
