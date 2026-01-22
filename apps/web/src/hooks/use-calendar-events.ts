import { useQuery } from "@tanstack/react-query";
import { useSupabase } from "@/lib/supabase-provider";
import type { CalendarEvent } from "@/components/event-card";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type BackendCalendarEvent = {
  id: string;
  title: string;
  description: string | null;
  start: string;
  end: string;
  location: string | null;
  attendees: number | null;
};

type BackendCalendarResponse = {
  events: BackendCalendarEvent[];
};

export function useCalendarEvents(options?: {
  timeMin?: Date;
  timeMax?: Date;
  maxResults?: number;
}) {
  const { googleAccessToken } = useSupabase();

  return useQuery<CalendarEvent[], Error>({
    queryKey: [
      "calendar-events",
      googleAccessToken,
      options?.timeMin?.toISOString(),
      options?.timeMax?.toISOString(),
    ],
    queryFn: async () => {
      if (!googleAccessToken) {
        throw new Error("No Google access token available");
      }

      const timeMin = options?.timeMin ?? new Date();
      const timeMax =
        options?.timeMax ?? new Date(Date.now() + 24 * 60 * 60 * 1000);
      const maxResults = options?.maxResults ?? 10;

      const params = new URLSearchParams({
        time_min: timeMin.toISOString(),
        time_max: timeMax.toISOString(),
        max_results: maxResults.toString(),
      });

      const response = await fetch(`${API_URL}/calendar/events?${params}`, {
        headers: {
          "X-Google-Token": googleAccessToken,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(
          error.detail || `Failed to fetch calendar events: ${response.status}`
        );
      }

      const data: BackendCalendarResponse = await response.json();

      // Transform backend response to CalendarEvent format
      return data.events.map((event) => ({
        id: event.id,
        title: event.title,
        description: event.description ?? undefined,
        start: new Date(event.start),
        end: new Date(event.end),
        location: event.location ?? undefined,
        attendees: event.attendees ?? undefined,
      }));
    },
    enabled: !!googleAccessToken,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });
}
