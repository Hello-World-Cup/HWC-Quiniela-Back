"""initial schema

Revision ID: 0000
Revises:
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("google_id", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("group", sa.String(1), nullable=True),
        sa.Column("flag_url", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_teams_id"), "teams", ["id"], unique=False)

    # --- matches ---
    match_status_enum = sa.Enum("pending", "in_progress", "finished", name="matchstatus")
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_a_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("team_b_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_a", sa.Integer(), nullable=True),
        sa.Column("result_b", sa.Integer(), nullable=True),
        sa.Column("status", match_status_enum, nullable=False, server_default="pending"),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("group", sa.String(1), nullable=True),
        sa.Column("round", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matches_id"), "matches", ["id"], unique=False)

    # --- predictions ---
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("predicted_score_a", sa.Integer(), nullable=False),
        sa.Column("predicted_score_b", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "match_id", name="uq_user_match"),
    )
    op.create_index(op.f("ix_predictions_id"), "predictions", ["id"], unique=False)
    op.create_index(op.f("ix_predictions_user_id"), "predictions", ["user_id"], unique=False)
    op.create_index(op.f("ix_predictions_match_id"), "predictions", ["match_id"], unique=False)


def downgrade() -> None:
    op.drop_table("predictions")
    op.drop_index(op.f("ix_matches_id"), table_name="matches")
    op.drop_table("matches")
    sa.Enum(name="matchstatus").drop(op.get_bind())
    op.drop_index(op.f("ix_teams_id"), table_name="teams")
    op.drop_table("teams")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_table("users")
