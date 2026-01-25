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
from sqlalchemy import select, update, and_, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models import CalendarEvent as CalendarEventModel
from app.models import CalendarSyncState as CalendarSyncStateModel
from app.models import HypeRecord as HypeRecordModel
from app.services.google_token_service import (
    GoogleTokenService,
    NoRefreshTokenError,
    TokenRefreshError,
)

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
        self.token_service = GoogleTokenService(settings)

    async def get_sync_state(self, db: AsyncSession, user_id: str) -> dict:
        """Get the sync state for a user."""
        try:
            stmt = select(CalendarSyncStateModel).where(
                CalendarSyncStateModel.user_id == user_id
            )
            result = await db.execute(stmt)
            state = result.scalar_one_or_none()
            if state:
                return {
                    "user_id": str(state.user_id),
                    "last_sync": state.last_sync.isoformat() if state.last_sync else None,
                    "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                }
            return {}
        except Exception:
            return {}

    async def update_sync_state(self, db: AsyncSession, user_id: str) -> None:
        """Update the sync state for a user."""
        now = datetime.now(timezone.utc)
        stmt = insert(CalendarSyncStateModel).values(
            user_id=user_id,
            last_sync=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "last_sync": now,
                "updated_at": now,
            },
        )
        await db.execute(stmt)
        await db.commit()

    async def should_sync(self, db: AsyncSession, user_id: str) -> bool:
        """Check if enough time has passed since last sync."""
        state = await self.get_sync_state(db, user_id)
        if not state or not state.get("last_sync"):
            return True

        last_sync = datetime.fromisoformat(state["last_sync"].replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - last_sync > MIN_SYNC_INTERVAL

    async def _fetch_events_from_google(
        self,
        db: AsyncSession,
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
        access_token = await self.token_service.get_access_token(db, user_id)
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
        self, db: AsyncSession, user_id: str, events: list[dict], is_incremental: bool = False
    ) -> SyncResult:
        """Store events in the database."""
        result = SyncResult(is_full_sync=not is_incremental)
        now = datetime.now(timezone.utc)

        for event in events:
            google_event_id = event.get("id")
            if not google_event_id:
                continue

            # Check if event is deleted
            if event.get("status") == "cancelled":
                # Mark as deleted in our database
                stmt = (
                    update(CalendarEventModel)
                    .where(
                        and_(
                            CalendarEventModel.user_id == user_id,
                            CalendarEventModel.google_event_id == google_event_id,
                        )
                    )
                    .values(is_deleted=True, synced_at=now)
                )
                await db.execute(stmt)
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

            # Upsert event using PostgreSQL ON CONFLICT
            stmt = insert(CalendarEventModel).values(
                user_id=user_id,
                google_event_id=google_event_id,
                title=event.get("summary", "Untitled Event"),
                description=event.get("description"),
                start_time=start_time,
                end_time=end_time,
                location=event.get("location"),
                attendees_count=(
                    len(event.get("attendees", [])) if event.get("attendees") else None
                ),
                etag=event.get("etag"),
                synced_at=now,
                is_deleted=False,
            ).on_conflict_do_update(
                constraint="unique_user_google_event",
                set_={
                    "title": event.get("summary", "Untitled Event"),
                    "description": event.get("description"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": event.get("location"),
                    "attendees_count": (
                        len(event.get("attendees", [])) if event.get("attendees") else None
                    ),
                    "etag": event.get("etag"),
                    "synced_at": now,
                    "is_deleted": False,
                },
            )
            await db.execute(stmt)

            # Check if it was an insert or update based on etag comparison
            # For simplicity, count all as "added" for full sync, "updated" for incremental
            if is_incremental:
                result.events_updated += 1
            else:
                result.events_added += 1

        await db.commit()
        return result

    async def sync_calendar(
        self, db: AsyncSession, user_id: str, force_full: bool = False
    ) -> SyncResult:
        """
        Sync calendar events for a user.

        Uses time-bounded sync with updatedMin for incremental updates:
        - Full sync: fetches all events in time window (-30 days to +90 days)
        - Incremental sync: fetches events updated since last sync

        Args:
            db: Database session
            user_id: The user's ID
            force_full: Force a full sync instead of incremental

        Returns:
            SyncResult with counts of added/updated/deleted events
        """
        state = await self.get_sync_state(db, user_id)
        last_sync = None
        if not force_full and state and state.get("last_sync"):
            last_sync = datetime.fromisoformat(
                state["last_sync"].replace("Z", "+00:00")
            )

        if last_sync:
            # Incremental sync - only get events updated since last sync
            logger.info(f"Starting incremental sync for user {user_id[:8]}... (since {last_sync})")
            events, _ = await self._fetch_events_from_google(
                db, user_id, updated_min=last_sync
            )
            result = await self._store_events(db, user_id, events, is_incremental=True)
        else:
            # Full sync - get all events in time window
            logger.info(f"Starting full sync for user {user_id[:8]}...")
            events, _ = await self._fetch_events_from_google(db, user_id)
            result = await self._store_events(db, user_id, events, is_incremental=False)
            result.is_full_sync = True

        # Update sync state
        await self.update_sync_state(db, user_id)

        logger.info(
            f"Sync complete for user {user_id[:8]}...: "
            f"added={result.events_added}, "
            f"updated={result.events_updated}, "
            f"deleted={result.events_deleted}"
        )
        return result

    async def get_cached_events(
        self,
        db: AsyncSession,
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
            db: Database session
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
        stmt = (
            select(CalendarEventModel)
            .where(
                and_(
                    CalendarEventModel.user_id == user_id,
                    CalendarEventModel.is_deleted == False,
                    CalendarEventModel.end_time > time_min,
                    CalendarEventModel.start_time <= time_max,
                )
            )
            .order_by(CalendarEventModel.start_time)
            .limit(max_results)
        )
        result = await db.execute(stmt)
        event_rows = result.scalars().all()

        if not event_rows:
            return []

        # Get google_event_ids to fetch latest hype
        google_event_ids = [row.google_event_id for row in event_rows]

        # Fetch latest hype records for these events
        # We get all hype records and will pick the latest per event
        hype_stmt = (
            select(HypeRecordModel)
            .where(
                and_(
                    HypeRecordModel.user_id == user_id,
                    HypeRecordModel.google_event_id.in_(google_event_ids),
                    HypeRecordModel.status.in_(["text_ready", "audio_ready"]),
                )
            )
            .order_by(HypeRecordModel.created_at.desc())
        )
        hype_result = await db.execute(hype_stmt)
        hype_rows = hype_result.scalars().all()

        # Build a map of google_event_id -> latest hype (first one per event since ordered desc)
        latest_hype_map: dict[str, LatestHypeData] = {}
        for hype_row in hype_rows:
            gid = hype_row.google_event_id
            if gid and gid not in latest_hype_map:
                latest_hype_map[gid] = LatestHypeData(
                    hype_text=hype_row.hype_text,
                    audio_url=hype_row.audio_url,
                    manager_style=hype_row.manager_style or "ferguson",
                )

        events = []
        for row in event_rows:
            google_event_id = row.google_event_id
            events.append(
                CachedEvent(
                    id=str(row.id),
                    user_id=str(row.user_id),
                    google_event_id=google_event_id,
                    title=row.title,
                    description=row.description,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    location=row.location,
                    attendees_count=row.attendees_count,
                    etag=row.etag,
                    synced_at=row.synced_at,
                    is_deleted=row.is_deleted,
                    latest_hype=latest_hype_map.get(google_event_id),
                )
            )

        return events


def get_calendar_sync_service() -> CalendarSyncService:
    """Get a CalendarSyncService instance."""
    settings = get_settings()
    return CalendarSyncService(settings)
