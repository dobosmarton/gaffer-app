from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.services.supabase_client import get_supabase_client

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


async def get_user_id_from_token(
    authorization: str = Header(...),
    settings: Settings = Depends(get_settings),
) -> str:
    """Extract and verify user ID from Supabase JWT."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    supabase = get_supabase_client(settings)

    try:
        # Verify the JWT and get user
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_google_access_token(
    user_id: str,
    settings: Settings,
) -> str:
    """Get a fresh Google access token using the stored refresh token."""
    supabase = get_supabase_client(settings)

    # Fetch refresh token from our user_google_tokens table
    try:
        response = supabase.table("user_google_tokens").select("refresh_token").eq("user_id", user_id).single().execute()
    except Exception:
        response = None

    if not response or not response.data:
        raise HTTPException(
            status_code=400,
            detail="No refresh token available. Please sign out and sign in again with Google."
        )

    refresh_token = response.data.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token available. Please sign out and sign in again with Google."
        )

    # Exchange refresh token for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if token_response.status_code != 200:
            error_data = token_response.json()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh Google token: {error_data.get('error_description', 'Unknown error')}"
            )

        token_data = token_response.json()
        return token_data["access_token"]


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 10,
    user_id: str = Depends(get_user_id_from_token),
    settings: Settings = Depends(get_settings),
):
    """Fetch calendar events from Google Calendar."""
    # Default to next 24 hours
    if time_min is None:
        time_min = datetime.now(timezone.utc)
    if time_max is None:
        time_max = time_min + timedelta(hours=24)

    # Get fresh access token
    access_token = await get_google_access_token(user_id, settings)

    # Fetch events from Google Calendar
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
        )

        if response.status_code != 200:
            error_data = response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch calendar events: {error_data.get('error', {}).get('message', 'Unknown error')}"
            )

        data = response.json()

    # Transform Google Calendar events to our format
    events = []
    for item in data.get("items", []):
        # Skip all-day events (no dateTime)
        start_data = item.get("start", {})
        end_data = item.get("end", {})

        if "dateTime" not in start_data:
            continue

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

    return CalendarEventsResponse(events=events)
