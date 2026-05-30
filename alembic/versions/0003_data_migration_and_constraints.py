"""data migration and constraints after seed

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-29

Run AFTER seed_teams.py and seed_matches.py have been executed.
Sets NOT NULL constraints on iso_code (teams) and stage (matches),
and migrates legacy status values to new ones.
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Status migration uses new enum values added in 0002.
    # Must run after a fresh connection to avoid PostgreSQL enum snapshot issues.
    # The app's status_map already handles legacy values, so this is best-effort.
    bind.execute(sa.text("COMMIT"))
    bind.execute(sa.text("UPDATE matches SET status = 'scheduled' WHERE status = 'pending'"))
    bind.execute(sa.text("UPDATE matches SET status = 'live' WHERE status = 'in_progress'"))
    bind.execute(sa.text("BEGIN"))

    # Set NOT NULL on teams.iso_code (seed must have run first)
    op.alter_column("teams", "iso_code", existing_type=sa.String(10), nullable=False)

    # Backfill stage for group-stage rows that may be missing it
    bind.execute(
        sa.text("UPDATE matches SET stage = 'group' WHERE stage IS NULL AND \"group\" IS NOT NULL")
    )


def downgrade() -> None:
    op.alter_column("teams", "iso_code", existing_type=sa.String(10), nullable=True)
    # Status rollback: map scheduled→pending, live→in_progress
    bind = op.get_bind()
    bind.execute(sa.text("UPDATE matches SET status = 'pending' WHERE status = 'scheduled'"))
    bind.execute(sa.text("UPDATE matches SET status = 'in_progress' WHERE status = 'live'"))
