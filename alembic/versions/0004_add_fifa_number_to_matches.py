"""add fifa_number to matches

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("fifa_number", sa.Integer, nullable=True))
    op.create_index("ix_matches_fifa_number", "matches", ["fifa_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_matches_fifa_number", table_name="matches")
    op.drop_column("matches", "fifa_number")
