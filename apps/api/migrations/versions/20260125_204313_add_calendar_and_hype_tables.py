"""add calendar and hype tables

Revision ID: 1de30f79bd89
Revises: 001
Create Date: 2026-01-25 20:43:13.490039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1de30f79bd89'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create calendar_events table
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_event_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.Text()),
        sa.Column("attendees_count", sa.Integer()),
        sa.Column("etag", sa.Text()),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "google_event_id", name="unique_user_google_event"),
    )
    op.create_index("idx_calendar_events_user_id", "calendar_events", ["user_id"])
    op.create_index("idx_calendar_events_user_start", "calendar_events", ["user_id", "start_time"])
    op.create_index("idx_calendar_events_google_id", "calendar_events", ["google_event_id"])

    # Enable RLS on calendar_events
    op.execute("ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY "Users can view own events" ON calendar_events
        FOR SELECT USING (auth.uid() = user_id)
    """)

    # Create hype_records table
    op.create_table(
        "hype_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calendar_event_id", postgresql.UUID(as_uuid=True)),
        sa.Column("google_event_id", sa.Text()),
        sa.Column("event_title", sa.Text(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("manager_style", sa.Text(), server_default="ferguson", nullable=False),
        sa.Column("hype_text", sa.Text()),
        sa.Column("audio_text", sa.Text()),
        sa.Column("audio_url", sa.Text()),
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["calendar_event_id"], ["calendar_events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hype_records_user_id", "hype_records", ["user_id"])
    op.create_index("idx_hype_records_calendar_event", "hype_records", ["calendar_event_id"])
    op.create_index("idx_hype_records_google_event", "hype_records", ["google_event_id"])
    op.create_index("idx_hype_records_user_created", "hype_records", ["user_id", "created_at"])

    # Enable RLS on hype_records
    op.execute("ALTER TABLE hype_records ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY "Users can view own hype records" ON hype_records
        FOR SELECT USING (auth.uid() = user_id)
    """)
    op.execute("""
        CREATE POLICY "Users can insert own hype records" ON hype_records
        FOR INSERT WITH CHECK (auth.uid() = user_id)
    """)
    op.execute("""
        CREATE POLICY "Users can update own hype records" ON hype_records
        FOR UPDATE USING (auth.uid() = user_id)
    """)

    # Create calendar_sync_state table
    op.create_table(
        "calendar_sync_state",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # Enable RLS on calendar_sync_state
    op.execute("ALTER TABLE calendar_sync_state ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY "Users can view own sync state" ON calendar_sync_state
        FOR SELECT USING (auth.uid() = user_id)
    """)


def downgrade() -> None:
    # Drop calendar_sync_state
    op.execute('DROP POLICY IF EXISTS "Users can view own sync state" ON calendar_sync_state')
    op.drop_table("calendar_sync_state")

    # Drop hype_records
    op.execute('DROP POLICY IF EXISTS "Users can update own hype records" ON hype_records')
    op.execute('DROP POLICY IF EXISTS "Users can insert own hype records" ON hype_records')
    op.execute('DROP POLICY IF EXISTS "Users can view own hype records" ON hype_records')
    op.drop_index("idx_hype_records_user_created", table_name="hype_records")
    op.drop_index("idx_hype_records_google_event", table_name="hype_records")
    op.drop_index("idx_hype_records_calendar_event", table_name="hype_records")
    op.drop_index("idx_hype_records_user_id", table_name="hype_records")
    op.drop_table("hype_records")

    # Drop calendar_events
    op.execute('DROP POLICY IF EXISTS "Users can view own events" ON calendar_events')
    op.drop_index("idx_calendar_events_google_id", table_name="calendar_events")
    op.drop_index("idx_calendar_events_user_start", table_name="calendar_events")
    op.drop_index("idx_calendar_events_user_id", table_name="calendar_events")
    op.drop_table("calendar_events")
