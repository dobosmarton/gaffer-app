"""Update RLS policies for SQLAlchemy direct access

When using SQLAlchemy directly instead of Supabase client, the auth.uid()
function doesn't work because there's no PostgREST context setting the JWT.

This migration adds policies that allow the application's database role
(authenticated via connection string) to perform all operations.
Authorization is handled at the application layer by filtering queries by user_id.

Revision ID: 002_rls_update
Revises: 1de30f79bd89
Create Date: 2026-01-25 22:00:00

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_rls_update"
down_revision: Union[str, None] = "1de30f79bd89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_google_tokens: Add full CRUD policies for authenticated role
    # The existing SELECT policy only works with auth.uid(), add service policies
    op.execute("""
        CREATE POLICY "Service can select tokens" ON user_google_tokens
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert tokens" ON user_google_tokens
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update tokens" ON user_google_tokens
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete tokens" ON user_google_tokens
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)

    # calendar_events: Add full CRUD policies
    op.execute("""
        CREATE POLICY "Service can select events" ON calendar_events
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert events" ON calendar_events
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update events" ON calendar_events
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete events" ON calendar_events
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)

    # hype_records: Add service policies (already has some user policies)
    op.execute("""
        CREATE POLICY "Service can select hype" ON hype_records
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert hype" ON hype_records
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update hype" ON hype_records
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete hype" ON hype_records
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)

    # calendar_sync_state: Add full CRUD policies
    op.execute("""
        CREATE POLICY "Service can select sync state" ON calendar_sync_state
        FOR SELECT TO authenticated, service_role, postgres
        USING (true)
    """)
    op.execute("""
        CREATE POLICY "Service can insert sync state" ON calendar_sync_state
        FOR INSERT TO authenticated, service_role, postgres
        WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can update sync state" ON calendar_sync_state
        FOR UPDATE TO authenticated, service_role, postgres
        USING (true) WITH CHECK (true)
    """)
    op.execute("""
        CREATE POLICY "Service can delete sync state" ON calendar_sync_state
        FOR DELETE TO authenticated, service_role, postgres
        USING (true)
    """)


def downgrade() -> None:
    # Drop all service policies

    # user_google_tokens
    op.execute('DROP POLICY IF EXISTS "Service can select tokens" ON user_google_tokens')
    op.execute('DROP POLICY IF EXISTS "Service can insert tokens" ON user_google_tokens')
    op.execute('DROP POLICY IF EXISTS "Service can update tokens" ON user_google_tokens')
    op.execute('DROP POLICY IF EXISTS "Service can delete tokens" ON user_google_tokens')

    # calendar_events
    op.execute('DROP POLICY IF EXISTS "Service can select events" ON calendar_events')
    op.execute('DROP POLICY IF EXISTS "Service can insert events" ON calendar_events')
    op.execute('DROP POLICY IF EXISTS "Service can update events" ON calendar_events')
    op.execute('DROP POLICY IF EXISTS "Service can delete events" ON calendar_events')

    # hype_records
    op.execute('DROP POLICY IF EXISTS "Service can select hype" ON hype_records')
    op.execute('DROP POLICY IF EXISTS "Service can insert hype" ON hype_records')
    op.execute('DROP POLICY IF EXISTS "Service can update hype" ON hype_records')
    op.execute('DROP POLICY IF EXISTS "Service can delete hype" ON hype_records')

    # calendar_sync_state
    op.execute('DROP POLICY IF EXISTS "Service can select sync state" ON calendar_sync_state')
    op.execute('DROP POLICY IF EXISTS "Service can insert sync state" ON calendar_sync_state')
    op.execute('DROP POLICY IF EXISTS "Service can update sync state" ON calendar_sync_state')
    op.execute('DROP POLICY IF EXISTS "Service can delete sync state" ON calendar_sync_state')
