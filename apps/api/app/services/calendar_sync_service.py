"""
Calendar Sync Service

Handles syncing calendar events from Google Calendar using time-bounded sync.
Events are cached in the database for faster access.

Sync strategy:
- Full sync: Fetches events from -30 days to +90 days
- Incremental sync: Uses updatedMin to get events changed since last sync
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import Settings, get_settings
from app.services.google_token_service import (
    GoogleTokenService,
    NoRefreshTokenError,
    TokenRefreshError,
    get_google_token_service,
)
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Sync every 5 minutes at most
MIN_SYNC_INTERVAL = timedelta(minutes=5)


class CalendarSyncError(Exception):
    """Base exception for calendar sync operations."""

    pass


@dataclass
class SyncResult:
    """Result of a calendar sync operation."""

    events_added: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    is_full_sync: bool = False


@dataclass
class LatestHypeData:
    """Latest hype data for an event."""

    hype_text: Optional[str]
    audio_url: Optional[str]
    manager_style: str


@dataclass
class CachedEvent:
    """Represents a cached calendar event."""

    id: str
    user_id: str
    google_event_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees_count: Optional[int]
    etag: Optional[str]
    synced_at: datetime
    is_deleted: bool
    latest_hype: Optional[LatestHypeData] = None


class CalendarSyncService:
    """Service for syncing calendar events from Google Calendar."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.supabase = get_supabase_client(settings)
        self.token_service = GoogleTokenService(settings)

    async def get_sync_state(self, user_id: str) -> dict:
        """Get the sync state for a user."""
        try:
            response = (
                self.supabase.table("calendar_sync_state")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return response.data or {}
        except Exception:
            return {}

    async def update_sync_state(self, user_id: str) -> None:
        """Update the sync state for a user."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "user_id": user_id,
            "last_sync": now,
            "updated_at": now,
        }
        self.supabase.table("calendar_sync_state").upsert(data).execute()

    async def should_sync(self, user_id: str) -> bool:
        """Check if enough time has passed since last sync."""
        state = await self.get_sync_state(user_id)
        if not state or not state.get("last_sync"):
            return True

        last_sync = datetime.fromisoformat(state["last_sync"].replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - last_sync > MIN_SYNC_INTERVAL

    async def _fetch_events_from_google(
        self,
        user_id: str,
        updated_min: Optional[datetime] = None,
    ) -> tuple[list[dict], bool]:
        """
        Fetch events from Google Calendar API with pagination support.

        Uses time boundaries to limit data:
        - timeMin: 30 days ago
        - timeMax: 90 days ahead

        For incremental updates, use updated_min to get only recently changed events.

        Returns:
            Tuple of (events, has_deleted)
        """
        access_token = await self.token_service.get_access_token(user_id)
        all_events: list[dict] = []
        page_token: Optional[str] = None

        # Time boundaries for sync
        time_min = datetime.now(timezone.utc) - timedelta(days=30)
        time_max = datetime.now(timezone.utc) + timedelta(days=90)

        async with httpx.AsyncClient() as client:
            while True:
                params: dict[str, str] = {
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": "250",
                    "timeMin": time_min.isoformat(),
                    "timeMax": time_max.isoformat(),
                }

                # For incremental sync, only get events updated since last sync
                if updated_min:
                    params["updatedMin"] = updated_min.isoformat()
                    # When using updatedMin, we need to include deleted events
                    params["showDeleted"] = "true"

                if page_token:
                    params["pageToken"] = page_token

                response = await client.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=30,
                )

                if response.status_code == 401:
                    raise TokenRefreshError("Access token invalid")

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Google Calendar API error: {error_msg}")
                    raise CalendarSyncError(f"Failed to fetch events: {error_msg}")

                data = response.json()
                all_events.extend(data.get("items", []))

                # Check for more pages
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

                logger.info(f"Fetching next page of events for user {user_id[:8]}...")

        # Check if any events are marked as cancelled (deleted)
        has_deleted = any(item.get("status") == "cancelled" for item in all_events)

        logger.info(f"Fetched {len(all_events)} events for user {user_id[:8]}...")
        return all_events, has_deleted

    async def _store_events(
        self, user_id: str, events: list[dict], is_incremental: bool = False
    ) -> SyncResult:
        """Store events in the database."""
        result = SyncResult(is_full_sync=not is_incremental)
        now = datetime.now(timezone.utc).isoformat()

        for event in events:
            google_event_id = event.get("id")
            if not google_event_id:
                continue

            # Check if event is deleted
            if event.get("status") == "cancelled":
                # Mark as deleted in our database
                self.supabase.table("calendar_events").update(
                    {"is_deleted": True, "synced_at": now}
                ).eq("user_id", user_id).eq("google_event_id", google_event_id).execute()
                result.events_deleted += 1
                continue

            # Parse event data
            start_data = event.get("start", {})
            end_data = event.get("end", {})

            # Skip all-day events (no dateTime)
            if "dateTime" not in start_data:
                continue

            try:
                start_time = datetime.fromisoformat(
                    start_data["dateTime"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    end_data["dateTime"].replace("Z", "+00:00")
                )
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse event {google_event_id}: {e}")
                continue

            event_data = {
                "user_id": user_id,
                "google_event_id": google_event_id,
                "title": event.get("summary", "Untitled Event"),
                "description": event.get("description"),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "location": event.get("location"),
                "attendees_count": (
                    len(event.get("attendees", [])) if event.get("attendees") else None
                ),
                "etag": event.get("etag"),
                "synced_at": now,
                "is_deleted": False,
            }

            # Upsert event
            response = (
                self.supabase.table("calendar_events")
                .upsert(event_data, on_conflict="user_id,google_event_id")
                .execute()
            )

            # Check if it was an insert or update based on etag comparison
            # For simplicity, count all as "added" for full sync, "updated" for incremental
            if is_incremental:
                result.events_updated += 1
            else:
                result.events_added += 1

        return result

    async def sync_calendar(
        self, user_id: str, force_full: bool = False
    ) -> SyncResult:
        """
        Sync calendar events for a user.

        Uses time-bounded sync with updatedMin for incremental updates:
        - Full sync: fetches all events in time window (-30 days to +90 days)
        - Incremental sync: fetches events updated since last sync

        Args:
            user_id: The user's ID
            force_full: Force a full sync instead of incremental

        Returns:
            SyncResult with counts of added/updated/deleted events
        """
        state = await self.get_sync_state(user_id)
        last_sync = None
        if not force_full and state and state.get("last_sync"):
            last_sync = datetime.fromisoformat(
                state["last_sync"].replace("Z", "+00:00")
            )

        if last_sync:
            # Incremental sync - only get events updated since last sync
            logger.info(f"Starting incremental sync for user {user_id[:8]}... (since {last_sync})")
            events, _ = await self._fetch_events_from_google(
                user_id, updated_min=last_sync
            )
            result = await self._store_events(user_id, events, is_incremental=True)
        else:
            # Full sync - get all events in time window
            logger.info(f"Starting full sync for user {user_id[:8]}...")
            events, _ = await self._fetch_events_from_google(user_id)
            result = await self._store_events(user_id, events, is_incremental=False)
            result.is_full_sync = True

        # Update sync state
        await self.update_sync_state(user_id)

        logger.info(
            f"Sync complete for user {user_id[:8]}...: "
            f"added={result.events_added}, "
            f"updated={result.events_updated}, "
            f"deleted={result.events_deleted}"
        )
        return result

    async def get_cached_events(
        self,
        user_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50,
    ) -> list[CachedEvent]:
        """
        Get cached events from the database.

        Returns events that:
        - Start within the time window, OR
        - Are currently ongoing (started before time_min but end after time_min)

        Args:
            user_id: The user's ID
            time_min: Reference time (defaults to now)
            time_max: Maximum start time (defaults to 24 hours from time_min)
            max_results: Maximum number of events to return

        Returns:
            List of cached calendar events
        """
        if time_min is None:
            time_min = datetime.now(timezone.utc)
        if time_max is None:
            time_max = time_min + timedelta(hours=24)

        # Get events that either:
        # 1. Start within the time window (start_time >= time_min AND start_time <= time_max)
        # 2. Are ongoing (start_time < time_min AND end_time > time_min)
        # Using OR filter: end_time > time_min AND start_time <= time_max
        response = (
            self.supabase.table("calendar_events")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .gt("end_time", time_min.isoformat())  # Event hasn't ended yet
            .lte("start_time", time_max.isoformat())  # Event starts before window ends
            .order("start_time")
            .limit(max_results)
            .execute()
        )

        if not response.data:
            return []

        # Get google_event_ids to fetch latest hype
        google_event_ids = [row["google_event_id"] for row in response.data]

        # Fetch latest hype records for these events
        # We get all hype records and will pick the latest per event
        hype_response = (
            self.supabase.table("hype_records")
            .select("google_event_id, hype_text, audio_url, manager_style, created_at")
            .eq("user_id", user_id)
            .in_("google_event_id", google_event_ids)
            .in_("status", ["text_ready", "audio_ready"])
            .order("created_at", desc=True)
            .execute()
        )

        # Build a map of google_event_id -> latest hype (first one per event since ordered desc)
        latest_hype_map: dict[str, LatestHypeData] = {}
        for hype_row in hype_response.data or []:
            gid = hype_row["google_event_id"]
            if gid not in latest_hype_map:
                latest_hype_map[gid] = LatestHypeData(
                    hype_text=hype_row.get("hype_text"),
                    audio_url=hype_row.get("audio_url"),
                    manager_style=hype_row.get("manager_style", "ferguson"),
                )

        events = []
        for row in response.data:
            google_event_id = row["google_event_id"]
            events.append(
                CachedEvent(
                    id=row["id"],
                    user_id=row["user_id"],
                    google_event_id=google_event_id,
                    title=row["title"],
                    description=row.get("description"),
                    start_time=datetime.fromisoformat(
                        row["start_time"].replace("Z", "+00:00")
                    ),
                    end_time=datetime.fromisoformat(
                        row["end_time"].replace("Z", "+00:00")
                    ),
                    location=row.get("location"),
                    attendees_count=row.get("attendees_count"),
                    etag=row.get("etag"),
                    synced_at=datetime.fromisoformat(
                        row["synced_at"].replace("Z", "+00:00")
                    ),
                    is_deleted=row.get("is_deleted", False),
                    latest_hype=latest_hype_map.get(google_event_id),
                )
            )

        return events


def get_calendar_sync_service() -> CalendarSyncService:
    """Get a CalendarSyncService instance."""
    settings = get_settings()
    return CalendarSyncService(settings)
