"""
Unit tests for UsageService.
"""

import pytest
from datetime import datetime, timezone
from freezegun import freeze_time

from app.services.usage_service import UsageService, UsageInfo
from app.models import HypeRecord, UserSubscription


@pytest.fixture
def usage_service():
    """Create a UsageService instance."""
    return UsageService()


@pytest.mark.integration
class TestGetOrCreateSubscription:
    """Tests for subscription creation. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_creates_free_subscription_for_new_user(
        self, usage_service, pg_session, test_user_id
    ):
        """Creates a free subscription for user without one."""
        user_id_str = str(test_user_id)
        subscription = await usage_service.get_or_create_subscription(
            pg_session, user_id_str
        )

        assert str(subscription.user_id) == user_id_str
        assert subscription.plan_type == "free"
        assert subscription.monthly_limit == 5

    @pytest.mark.asyncio
    async def test_returns_existing_subscription(
        self, usage_service, pg_session, test_user_id
    ):
        """Returns existing subscription without creating new one."""
        user_id_str = str(test_user_id)
        # Create first
        sub1 = await usage_service.get_or_create_subscription(
            pg_session, user_id_str
        )

        # Get again
        sub2 = await usage_service.get_or_create_subscription(
            pg_session, user_id_str
        )

        assert sub1.id == sub2.id

    @pytest.mark.asyncio
    async def test_different_users_get_different_subscriptions(
        self, usage_service, pg_session
    ):
        """Different users get their own subscriptions."""
        from uuid import uuid4

        user1_id = str(uuid4())
        user2_id = str(uuid4())

        sub1 = await usage_service.get_or_create_subscription(pg_session, user1_id)
        sub2 = await usage_service.get_or_create_subscription(pg_session, user2_id)

        assert sub1.id != sub2.id
        assert str(sub1.user_id) == user1_id
        assert str(sub2.user_id) == user2_id


@pytest.mark.integration
class TestGetMonthlyUsage:
    """Tests for monthly usage counting. Requires PostgreSQL."""

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_counts_successful_generations_this_month(
        self, usage_service, pg_session, test_user_id
    ):
        """Counts only successful hype records from current month."""
        user_id_str = str(test_user_id)
        now = datetime.now(timezone.utc)

        # Create some hype records with successful status
        for i in range(3):
            record = HypeRecord(
                user_id=user_id_str,
                event_title=f"Event {i}",
                event_time=now,
                manager_style="ferguson",
                status="text_ready",
                created_at=now,
                updated_at=now,
            )
            pg_session.add(record)

        # Add one with error status (should not count)
        error_record = HypeRecord(
            user_id=user_id_str,
            event_title="Error Event",
            event_time=now,
            manager_style="ferguson",
            status="error",
            created_at=now,
            updated_at=now,
        )
        pg_session.add(error_record)
        await pg_session.commit()

        usage = await usage_service.get_monthly_usage(pg_session, user_id_str)

        assert usage == 3  # Only successful ones

    @pytest.mark.asyncio
    @freeze_time("2024-02-15T10:00:00Z")
    async def test_does_not_count_previous_month(
        self, usage_service, pg_session, test_user_id
    ):
        """Does not count records from previous month."""
        user_id_str = str(test_user_id)
        # Create record from January (previous month)
        jan_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        old_record = HypeRecord(
            user_id=user_id_str,
            event_title="Old Event",
            event_time=jan_time,
            manager_style="ferguson",
            status="text_ready",
            created_at=jan_time,
            updated_at=jan_time,
        )
        pg_session.add(old_record)
        await pg_session.commit()

        usage = await usage_service.get_monthly_usage(pg_session, user_id_str)

        assert usage == 0

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_counts_audio_ready_status(
        self, usage_service, pg_session, test_user_id
    ):
        """Counts records with audio_ready status."""
        user_id_str = str(test_user_id)
        now = datetime.now(timezone.utc)

        record = HypeRecord(
            user_id=user_id_str,
            event_title="Event",
            event_time=now,
            manager_style="ferguson",
            status="audio_ready",
            created_at=now,
            updated_at=now,
        )
        pg_session.add(record)
        await pg_session.commit()

        usage = await usage_service.get_monthly_usage(pg_session, user_id_str)

        assert usage == 1

    @pytest.mark.asyncio
    async def test_returns_zero_for_new_user(
        self, usage_service, pg_session, test_user_id
    ):
        """Returns 0 for user with no records."""
        user_id_str = str(test_user_id)
        usage = await usage_service.get_monthly_usage(pg_session, user_id_str)

        assert usage == 0


@pytest.mark.integration
class TestGetUsageInfo:
    """Tests for getting complete usage info. Requires PostgreSQL."""

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_returns_complete_usage_info(
        self, usage_service, pg_session, test_user_id
    ):
        """Returns complete UsageInfo dataclass."""
        user_id_str = str(test_user_id)
        info = await usage_service.get_usage_info(pg_session, user_id_str)

        assert isinstance(info, UsageInfo)
        assert info.used == 0
        assert info.limit == 5
        assert info.plan == "free"
        assert info.can_generate is True
        assert info.resets_at == datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    @freeze_time("2024-12-15T10:00:00Z")
    async def test_resets_at_handles_december(
        self, usage_service, pg_session, test_user_id
    ):
        """Reset date correctly handles December -> January transition."""
        user_id_str = str(test_user_id)
        info = await usage_service.get_usage_info(pg_session, user_id_str)

        # Should reset on January 1st of next year
        assert info.resets_at == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_can_generate_is_false_at_limit(
        self, usage_service, pg_session, test_user_id
    ):
        """can_generate is False when at monthly limit."""
        user_id_str = str(test_user_id)
        now = datetime.now(timezone.utc)

        # Create 5 records (free tier limit)
        for i in range(5):
            record = HypeRecord(
                user_id=user_id_str,
                event_title=f"Event {i}",
                event_time=now,
                manager_style="ferguson",
                status="text_ready",
                created_at=now,
                updated_at=now,
            )
            pg_session.add(record)
        await pg_session.commit()

        info = await usage_service.get_usage_info(pg_session, user_id_str)

        assert info.used == 5
        assert info.limit == 5
        assert info.can_generate is False


@pytest.mark.integration
class TestCheckCanGenerate:
    """Tests for checking if user can generate. Requires PostgreSQL."""

    @pytest.mark.asyncio
    async def test_can_generate_when_under_limit(
        self, usage_service, pg_session, test_user_id
    ):
        """User can generate when under monthly limit."""
        user_id_str = str(test_user_id)
        can, used, limit = await usage_service.check_can_generate(
            pg_session, user_id_str
        )

        assert can is True
        assert used == 0
        assert limit == 5

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_cannot_generate_when_at_limit(
        self, usage_service, pg_session, test_user_id
    ):
        """User cannot generate when at monthly limit."""
        user_id_str = str(test_user_id)
        now = datetime.now(timezone.utc)

        # Create 5 records (free tier limit)
        for i in range(5):
            record = HypeRecord(
                user_id=user_id_str,
                event_title=f"Event {i}",
                event_time=now,
                manager_style="ferguson",
                status="text_ready",
                created_at=now,
                updated_at=now,
            )
            pg_session.add(record)
        await pg_session.commit()

        can, used, limit = await usage_service.check_can_generate(
            pg_session, user_id_str
        )

        assert can is False
        assert used == 5
        assert limit == 5

    @pytest.mark.asyncio
    @freeze_time("2024-01-15T10:00:00Z")
    async def test_can_generate_when_under_limit_with_some_usage(
        self, usage_service, pg_session, test_user_id
    ):
        """User can generate when under limit but has some usage."""
        user_id_str = str(test_user_id)
        now = datetime.now(timezone.utc)

        # Create 3 records (under 5 limit)
        for i in range(3):
            record = HypeRecord(
                user_id=user_id_str,
                event_title=f"Event {i}",
                event_time=now,
                manager_style="ferguson",
                status="text_ready",
                created_at=now,
                updated_at=now,
            )
            pg_session.add(record)
        await pg_session.commit()

        can, used, limit = await usage_service.check_can_generate(
            pg_session, user_id_str
        )

        assert can is True
        assert used == 3
        assert limit == 5
