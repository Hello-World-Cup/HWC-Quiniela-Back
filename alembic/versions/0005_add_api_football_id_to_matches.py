"""add api_football_id to matches

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("api_football_id", sa.Integer(), nullable=True))
    op.create_index("ix_matches_api_football_id", "matches", ["api_football_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_matches_api_football_id", table_name="matches")
    op.drop_column("matches", "api_football_id")
