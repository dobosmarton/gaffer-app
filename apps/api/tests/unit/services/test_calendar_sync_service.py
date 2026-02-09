"""
Unit tests for CalendarSyncService.
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import httpx
import respx

from app.services.calendar_sync_service import (
    CalendarSyncService,
    CalendarSyncError,
    InsufficientScopeError,
)


@pytest.fixture
def calendar_sync_service(test_settings, cache_service):
    """Create a CalendarSyncService instance for testing."""
    return CalendarSyncService(test_settings, cache_service)


class TestFetchEventsFromGoogle:
    """Tests for Google Calendar API error handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_403_raises_insufficient_scope_error(
        self, calendar_sync_service, db_session, test_user_id, cache_service
    ):
        """HTTP 403 from Google Calendar API raises InsufficientScopeError."""
        user_id = str(test_user_id)

        # Pre-cache an access token so we skip token refresh
        await cache_service.set(
            f"google_access_token:{user_id}", "fake-access-token", ttl=timedelta(minutes=50)
        )

        respx.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        ).mock(
            return_value=httpx.Response(
                403,
                json={
                    "error": {
                        "code": 403,
                        "message": "Request had insufficient authentication scopes.",
                        "errors": [
                            {
                                "domain": "global",
                                "reason": "insufficientPermissions",
                                "message": "Insufficient Permission",
                            }
                        ],
                    }
                },
            )
        )

        with pytest.raises(InsufficientScopeError):
            await calendar_sync_service._fetch_events_from_google(db_session, user_id)

        # Verify access token cache was cleared
        cached = await cache_service.get(f"google_access_token:{user_id}")
        assert cached is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_insufficient_scope_is_calendar_sync_error_subclass(self):
        """InsufficientScopeError is a subclass of CalendarSyncError."""
        assert issubclass(InsufficientScopeError, CalendarSyncError)
