from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

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


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    x_google_token: str = Header(..., alias="X-Google-Token"),
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 10,
):
    """Fetch calendar events from Google Calendar.

    The Google access token must be provided via the X-Google-Token header.
    This token is obtained from the frontend after OAuth login.
    """
    # Default to next 24 hours
    if time_min is None:
        time_min = datetime.now(timezone.utc)
    if time_max is None:
        time_max = time_min + timedelta(hours=24)

    access_token = x_google_token

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
