import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.rate_limiter import limiter
from app.routers.auth import get_user_id_from_token
from app.services.database import get_db
from app.services.calendar_sync_service import (
    CalendarSyncError,
    CalendarSyncService,
    InsufficientScopeError,
    get_calendar_sync_service,
)
from app.types import ManagerStyle
from app.services.google_token_service import (
    GoogleTokenService,
    NoRefreshTokenError,
    TokenRefreshError,
    get_google_token_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class LatestHype(BaseModel):
    """Latest hype data for a calendar event."""
    hype_text: Optional[str] = None
    audio_url: Optional[str] = None
    manager_style: ManagerStyle = "ferguson"


class CalendarEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None
    attendees: Optional[int] = None
    latest_hype: Optional[LatestHype] = None
    # Importance scoring fields
    importance_score: Optional[int] = None
    importance_reason: Optional[str] = None
    importance_category: Optional[str] = None


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEvent]
    needs_google_auth: bool = False
    from_cache: bool = False
    last_sync: Optional[datetime] = None


class CalendarErrorResponse(BaseModel):
    detail: str
    needs_google_auth: bool = False


class SyncResponse(BaseModel):
    success: bool
    events_added: int
    events_updated: int
    events_deleted: int
    is_full_sync: bool


@router.post("/sync", response_model=SyncResponse)
@limiter.limit("10/minute")
async def sync_calendar(
    request: Request,
    force_full: bool = False,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    sync_service: CalendarSyncService = Depends(get_calendar_sync_service),
):
    """Sync calendar events from Google Calendar.

    This endpoint triggers a sync operation that fetches events from Google
    and stores them in the database. Uses incremental sync when possible.

    Args:
        force_full: Force a full sync instead of incremental
    """
    try:
        result = await sync_service.sync_calendar(db, user_id, force_full=force_full)
        return SyncResponse(
            success=True,
            events_added=result.events_added,
            events_updated=result.events_updated,
            events_deleted=result.events_deleted,
            is_full_sync=result.is_full_sync,
        )
    except NoRefreshTokenError:
        logger.info(f"User {user_id[:8]}... needs to authenticate with Google")
        raise HTTPException(
            status_code=401,
            detail={"message": "Google authentication required", "needs_google_auth": True},
        )
    except TokenRefreshError as e:
        logger.error(f"Token refresh failed for user {user_id[:8]}...: {e}")
        raise HTTPException(
            status_code=401,
            detail={"message": "Google authentication expired", "needs_google_auth": True},
        )
    except InsufficientScopeError as e:
        logger.warning(f"Insufficient scope for user {user_id[:8]}...: {e}")
        raise HTTPException(
            status_code=403,
            detail={"message": "Calendar permission not granted. Please reconnect Google.", "needs_google_auth": True},
        )
    except CalendarSyncError as e:
        logger.error(f"Calendar sync error for user {user_id[:8]}...: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to sync calendar events",
        )


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 10,
    use_cache: bool = True,
    user_id: str = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
    token_service: GoogleTokenService = Depends(get_google_token_service),
    sync_service: CalendarSyncService = Depends(get_calendar_sync_service),
):
    """Fetch calendar events.

    By default, returns cached events from the database. Set use_cache=false
    to fetch directly from Google Calendar API.

    Requires Supabase JWT authentication via Authorization header.
    """
    # Default to next 24 hours
    if time_min is None:
        time_min = datetime.now(timezone.utc)
    if time_max is None:
        time_max = time_min + timedelta(hours=24)

    # If using cache, return cached events
    if use_cache:
        try:
            cached_events = await sync_service.get_cached_events(
                db, user_id, time_min, time_max, max_results
            )

            # Get last sync time
            sync_state = await sync_service.get_sync_state(db, user_id)
            last_sync = None
            if sync_state and sync_state.get("last_sync"):
                last_sync = datetime.fromisoformat(
                    sync_state["last_sync"].replace("Z", "+00:00")
                )

            # Auto-sync if cache is empty and never synced before
            if not cached_events and not last_sync:
                logger.info(f"Empty cache and no sync history for user {user_id[:8]}..., triggering auto-sync")
                try:
                    await sync_service.sync_calendar(db, user_id, force_full=True)
                except InsufficientScopeError:
                    raise HTTPException(
                        status_code=403,
                        detail={"message": "Calendar permission not granted. Please reconnect Google.", "needs_google_auth": True},
                    )
                except (NoRefreshTokenError, TokenRefreshError):
                    raise HTTPException(
                        status_code=401,
                        detail={"message": "Google authentication required", "needs_google_auth": True},
                    )
                except CalendarSyncError as e:
                    logger.warning(f"Auto-sync failed for user {user_id[:8]}...: {e}")
                    # Fall through — return empty cache rather than failing
                # Re-fetch from cache after sync
                cached_events = await sync_service.get_cached_events(
                    db, user_id, time_min, time_max, max_results
                )
                sync_state = await sync_service.get_sync_state(db, user_id)
                if sync_state and sync_state.get("last_sync"):
                    last_sync = datetime.fromisoformat(
                        sync_state["last_sync"].replace("Z", "+00:00")
                    )

            events = [
                CalendarEvent(
                    id=e.google_event_id,
                    title=e.title,
                    description=e.description,
                    start=e.start_time,
                    end=e.end_time,
                    location=e.location,
                    attendees=e.attendees_count,
                    latest_hype=LatestHype(
                        hype_text=e.latest_hype.hype_text,
                        audio_url=e.latest_hype.audio_url,
                        manager_style=e.latest_hype.manager_style,
                    ) if e.latest_hype else None,
                    importance_score=e.importance_score,
                    importance_reason=e.importance_reason,
                    importance_category=e.importance_category,
                )
                for e in cached_events
            ]

            return CalendarEventsResponse(
                events=events,
                from_cache=True,
                last_sync=last_sync,
            )
        except (SQLAlchemyError, ValueError) as e:
            logger.warning(f"Failed to get cached events, falling back to Google: {e}")
            # Fall through to fetch from Google

    # Get access token from secure storage (handles refresh automatically)
    try:
        access_token = await token_service.get_access_token(db, user_id)
    except NoRefreshTokenError:
        logger.info(f"User {user_id[:8]}... needs to authenticate with Google")
        raise HTTPException(
            status_code=401,
            detail={"message": "Google authentication required", "needs_google_auth": True},
        )
    except TokenRefreshError as e:
        logger.error(f"Token refresh failed for user {user_id[:8]}...: {e}")
        raise HTTPException(
            status_code=401,
            detail={"message": "Google authentication expired", "needs_google_auth": True},
        )

    # Fetch events from Google Calendar
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "maxResults": max_results,
                "singleEvents": "true",
                "orderBy": "startTime",
            }

            response = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
            )

            if response.status_code == 401:
                # Token was invalid - clear cache and ask for re-auth
                logger.warning(f"Google API rejected token for user {user_id[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail={"message": "Google authentication expired", "needs_google_auth": True},
                )

            if response.status_code == 403:
                logger.warning(f"Google Calendar API 403 for user {user_id[:8]}... (direct fetch)")
                raise HTTPException(
                    status_code=403,
                    detail={"message": "Calendar permission not granted. Please reconnect Google.", "needs_google_auth": True},
                )

            if response.status_code == 429:
                logger.warning("Google Calendar API rate limit hit")
                raise HTTPException(
                    status_code=429,
                    detail="Calendar API rate limit exceeded. Please try again later.",
                )

            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logger.error(f"Google Calendar API error: {error_msg}")
                raise HTTPException(
                    status_code=502,
                    detail="Failed to fetch calendar events from Google",
                )

            data = response.json()

    except httpx.TimeoutException:
        logger.error("Google Calendar API timeout")
        raise HTTPException(
            status_code=504,
            detail="Calendar request timed out. Please try again.",
        )
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error(f"Unexpected error fetching calendar: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred",
        )

    # Transform Google Calendar events to our format
    events = []
    for item in data.get("items", []):
        # Skip all-day events (no dateTime)
        start_data = item.get("start", {})
        end_data = item.get("end", {})

        if "dateTime" not in start_data:
            continue

        try:
            events.append(
                CalendarEvent(
                    id=item["id"],
                    title=item.get("summary", "Untitled Event"),
                    description=item.get("description"),
                    start=datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00")),
                    end=datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00")),
                    location=item.get("location"),
                    attendees=len(item.get("attendees", [])) if item.get("attendees") else None,
                )
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to parse event {item.get('id', 'unknown')}: {e}")
            continue

    return CalendarEventsResponse(events=events, from_cache=False)
