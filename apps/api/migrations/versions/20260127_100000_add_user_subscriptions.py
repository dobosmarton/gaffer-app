"""Add user_subscriptions table for usage limits

Revision ID: 003_user_subscriptions
Revises: 002_rls_update
Create Date: 2026-01-27 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "003_user_subscriptions"
down_revision: Union[str, None] = "002_rls_update"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_subscriptions table
    op.create_table(
        "user_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_type", sa.Text(), server_default="free", nullable=False),
        sa.Column("monthly_limit", sa.Integer(), server_default="5", nullable=False),
        sa.Column("stripe_customer_id", sa.Text(), nullable=True),
        sa.Column("stripe_subscription_id", sa.Text(), nullable=True),
        sa.Column("stripe_status", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="unique_user_subscription"),
    )
    op.create_index("idx_user_subscriptions_user_id", "user_subscriptions", ["user_id"])
    op.create_index(
        "idx_user_subscriptions_stripe_customer",
        "user_subscriptions",
        ["stripe_customer_id"],
    )

    # Enable RLS
    op.execute("ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY")

    # User policies (for direct Supabase client access if needed)
    op.execute("""
        CREATE POLICY "Users can view own subscription" ON user_subscriptions
        FOR SELECT USING (auth.uid() = user_id)
    """)

    # Service role policies (for SQLAlchemy direct access)
    op.execute("""
        CREATE POLICY "Service can select subscriptions" ON user_subscriptions
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert subscriptions" ON user_subscriptions
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update subscriptions" ON user_subscriptions
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete subscriptions" ON user_subscriptions
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)


def downgrade() -> None:
    # Drop policies
    op.execute(
        'DROP POLICY IF EXISTS "Users can view own subscription" ON user_subscriptions'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can select subscriptions" ON user_subscriptions'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can insert subscriptions" ON user_subscriptions'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can update subscriptions" ON user_subscriptions'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Service can delete subscriptions" ON user_subscriptions'
    )

    # Drop indexes
    op.drop_index(
        "idx_user_subscriptions_stripe_customer", table_name="user_subscriptions"
    )
    op.drop_index("idx_user_subscriptions_user_id", table_name="user_subscriptions")

    # Drop table
    op.drop_table("user_subscriptions")
