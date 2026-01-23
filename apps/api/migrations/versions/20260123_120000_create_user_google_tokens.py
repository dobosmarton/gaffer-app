"""Create user_google_tokens table

Revision ID: 001
Revises:
Create Date: 2026-01-23 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_google_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "idx_user_google_tokens_user_id",
        "user_google_tokens",
        ["user_id"],
    )

    # Enable Row Level Security
    op.execute("ALTER TABLE user_google_tokens ENABLE ROW LEVEL SECURITY")

    # Create RLS policy for users to view their own tokens
    op.execute("""
        CREATE POLICY "Users can view own tokens" ON user_google_tokens
        FOR SELECT USING (auth.uid() = user_id)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS \"Users can view own tokens\" ON user_google_tokens")
    op.drop_index("idx_user_google_tokens_user_id", table_name="user_google_tokens")
    op.drop_table("user_google_tokens")
