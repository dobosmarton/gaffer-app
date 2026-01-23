import type { CalendarEvent } from "@/components/event-card";
import { useSupabase } from "@/lib/supabase-provider";
import { useQuery } from "@tanstack/react-query";

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
  needs_google_auth?: boolean;
};

type BackendErrorResponse = {
  detail: string | { message: string; needs_google_auth?: boolean };
};

export class NeedsGoogleAuthError extends Error {
  constructor(message: string = "Google authentication required") {
    super(message);
    this.name = "NeedsGoogleAuthError";
  }
}

export function useCalendarEvents(options?: {
  timeMin?: Date;
  timeMax?: Date;
  maxResults?: number;
}) {
  const { session, needsGoogleAuth } = useSupabase();

  return useQuery<CalendarEvent[], Error>({
    queryKey: [
      "calendar-events",
      session?.user?.id,
      options?.timeMin?.toISOString(),
      options?.timeMax?.toISOString(),
    ],
    queryFn: async () => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const timeMin = options?.timeMin ?? new Date();
      const timeMax = options?.timeMax ?? new Date(Date.now() + 24 * 60 * 60 * 1000);
      const maxResults = options?.maxResults ?? 10;

      const params = new URLSearchParams({
        time_min: timeMin.toISOString(),
        time_max: timeMax.toISOString(),
        max_results: maxResults.toString(),
      });

      const response = await fetch(`${API_URL}/calendar/events?${params}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const error: BackendErrorResponse = await response.json().catch(() => ({
          detail: "Unknown error",
        }));

        // Check if this is a "needs Google auth" error
        const detail = error.detail;
        if (typeof detail === "object" && detail.needs_google_auth) {
          throw new NeedsGoogleAuthError(detail.message);
        }

        const message = typeof detail === "string" ? detail : detail.message || "Unknown error";
        throw new Error(message);
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
    // Only enable if we have a session AND we don't need Google auth
    enabled: !!session?.access_token && !needsGoogleAuth,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
    retry: (failureCount, error) => {
      // Don't retry if user needs to authenticate with Google
      if (error instanceof NeedsGoogleAuthError) {
        return false;
      }
      return failureCount < 3;
    },
  });
}
