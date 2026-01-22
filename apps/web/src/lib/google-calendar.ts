import type { CalendarEvent } from "@/components/event-card";

const CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3";

type GoogleCalendarEvent = {
  id: string;
  summary?: string;
  description?: string;
  start: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  location?: string;
  attendees?: Array<{ email: string; responseStatus?: string }>;
};

type GoogleCalendarListResponse = {
  items: GoogleCalendarEvent[];
  nextPageToken?: string;
};

export async function fetchCalendarEvents(
  accessToken: string,
  options?: {
    timeMin?: Date;
    timeMax?: Date;
    maxResults?: number;
  }
): Promise<CalendarEvent[]> {
  const timeMin = options?.timeMin ?? new Date();
  const timeMax = options?.timeMax ?? new Date(Date.now() + 24 * 60 * 60 * 1000); // Next 24 hours
  const maxResults = options?.maxResults ?? 10;

  const params = new URLSearchParams({
    timeMin: timeMin.toISOString(),
    timeMax: timeMax.toISOString(),
    maxResults: maxResults.toString(),
    singleEvents: "true",
    orderBy: "startTime",
  });

  const response = await fetch(
    `${CALENDAR_API_BASE}/calendars/primary/events?${params}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.error?.message || `Failed to fetch calendar events: ${response.status}`
    );
  }

  const data: GoogleCalendarListResponse = await response.json();

  return data.items
    .filter((event) => event.start?.dateTime) // Filter out all-day events for now
    .map((event) => transformEvent(event));
}

function transformEvent(event: GoogleCalendarEvent): CalendarEvent {
  const start = event.start.dateTime
    ? new Date(event.start.dateTime)
    : new Date(event.start.date!);

  const end = event.end.dateTime
    ? new Date(event.end.dateTime)
    : new Date(event.end.date!);

  return {
    id: event.id,
    title: event.summary || "Untitled Event",
    description: event.description,
    start,
    end,
    location: event.location,
    attendees: event.attendees?.length,
  };
}
