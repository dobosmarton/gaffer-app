"""Add importance scoring columns to calendar_events

Revision ID: 005_importance_score
Revises: 004_upgrade_interests
Create Date: 2026-01-30 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_importance_score"
down_revision: Union[str, None] = "004_upgrade_interests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add importance scoring columns to calendar_events
    op.add_column(
        "calendar_events",
        sa.Column("importance_score", sa.Integer(), nullable=True),
    )
    op.add_column(
        "calendar_events",
        sa.Column("importance_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "calendar_events",
        sa.Column("importance_category", sa.Text(), nullable=True),
    )
    op.add_column(
        "calendar_events",
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index for filtering by importance
    op.create_index(
        "idx_calendar_events_importance",
        "calendar_events",
        ["user_id", "importance_score"],
    )


def downgrade() -> None:
    # Drop importance columns from calendar_events
    op.drop_index("idx_calendar_events_importance", table_name="calendar_events")
    op.drop_column("calendar_events", "scored_at")
    op.drop_column("calendar_events", "importance_category")
    op.drop_column("calendar_events", "importance_reason")
    op.drop_column("calendar_events", "importance_score")
