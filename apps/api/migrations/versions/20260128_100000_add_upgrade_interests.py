"""Add upgrade_interests table for tracking paid plan interest

Revision ID: 004_upgrade_interests
Revises: 003_user_subscriptions
Create Date: 2026-01-28 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "004_upgrade_interests"
down_revision: Union[str, None] = "003_user_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create upgrade_interests table
    op.create_table(
        "upgrade_interests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="unique_upgrade_interest_user"),
    )
    op.create_index("idx_upgrade_interests_user_id", "upgrade_interests", ["user_id"])

    # Enable RLS
    op.execute("ALTER TABLE upgrade_interests ENABLE ROW LEVEL SECURITY")

    # User policies (for direct Supabase client access if needed)
    op.execute("""
        CREATE POLICY "Users can view own interest" ON upgrade_interests
        FOR SELECT USING (auth.uid() = user_id)
    """)

    # Service role policies (for SQLAlchemy direct access)
    op.execute("""
        CREATE POLICY "Service can select interests" ON upgrade_interests
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert interests" ON upgrade_interests
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update interests" ON upgrade_interests
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete interests" ON upgrade_interests
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)


def downgrade() -> None:
    # Drop policies
    op.execute(
        'DROP POLICY IF EXISTS "Users can view own interest" ON upgrade_interests'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can select interests" ON upgrade_interests'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can insert interests" ON upgrade_interests'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can update interests" ON upgrade_interests'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can delete interests" ON upgrade_interests'
    )

    # Drop indexes
    op.drop_index("idx_upgrade_interests_user_id", table_name="upgrade_interests")

    # Drop table
    op.drop_table("upgrade_interests")
