import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.routers.auth import get_user_id_from_token
from app.services.google_token_service import (
    GoogleTokenService,
    NoRefreshTokenError,
    TokenRefreshError,
    get_google_token_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CalendarEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None
    attendees: Optional[int] = None


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEvent]
    needs_google_auth: bool = False


class CalendarErrorResponse(BaseModel):
    detail: str
    needs_google_auth: bool = False


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 10,
    user_id: str = Depends(get_user_id_from_token),
    token_service: GoogleTokenService = Depends(get_google_token_service),
):
    """Fetch calendar events from Google Calendar.

    Requires Supabase JWT authentication via Authorization header.
    The backend retrieves and manages Google tokens securely.
    """
    # Default to next 24 hours
    if time_min is None:
        time_min = datetime.now(timezone.utc)
    if time_max is None:
        time_max = time_min + timedelta(hours=24)

    # Get access token from secure storage (handles refresh automatically)
    try:
        access_token = await token_service.get_access_token(user_id)
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
    except Exception as e:
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

    return CalendarEventsResponse(events=events)
