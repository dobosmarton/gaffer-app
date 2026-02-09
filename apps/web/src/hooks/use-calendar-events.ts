import { useEffect } from "react";
import type { CalendarEvent } from "@/components/event-card";
import { useSupabase } from "@/lib/supabase-provider";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type LatestHype = {
  hype_text: string | null;
  audio_url: string | null;
  manager_style: string;
};

type BackendCalendarEvent = {
  id: string;
  title: string;
  description: string | null;
  start: string;
  end: string;
  location: string | null;
  attendees: number | null;
  latest_hype: LatestHype | null;
  // Importance scoring fields
  importance_score: number | null;
  importance_reason: string | null;
  importance_category: string | null;
};

type BackendCalendarResponse = {
  events: BackendCalendarEvent[];
  needs_google_auth?: boolean;
  from_cache?: boolean;
  last_sync?: string | null;
};

type BackendErrorResponse = {
  detail: string | { message: string; needs_google_auth?: boolean };
};

type SyncResponse = {
  success: boolean;
  events_added: number;
  events_updated: number;
  events_deleted: number;
  is_full_sync: boolean;
};

export class NeedsGoogleAuthError extends Error {
  constructor(message: string = "Google authentication required") {
    super(message);
    this.name = "NeedsGoogleAuthError";
  }
}

export const useCalendarSync = () => {
  const { session } = useSupabase();
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error, { forceFull?: boolean }>({
    mutationFn: async ({ forceFull = false }) => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const params = new URLSearchParams();
      if (forceFull) {
        params.set("force_full", "true");
      }

      const response = await fetch(`${API_URL}/calendar/sync?${params}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const error: BackendErrorResponse = await response.json().catch(() => ({
          detail: "Unknown error",
        }));
        const detail = error.detail;
        if (typeof detail === "object" && detail.needs_google_auth) {
          throw new NeedsGoogleAuthError(detail.message);
        }
        const message = typeof detail === "string" ? detail : detail.message || "Unknown error";
        throw new Error(message);
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate calendar events query to refetch
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });
};

export const useCalendarEvents = (options?: {
  timeMin?: Date;
  timeMax?: Date;
  maxResults?: number;
  useCache?: boolean;
}) => {
  const { session, needsGoogleAuth, setGoogleAuthNeeded } = useSupabase();

  const query = useQuery<CalendarEvent[], Error>({
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

      const useCache = options?.useCache ?? true;

      const params = new URLSearchParams({
        time_min: timeMin.toISOString(),
        time_max: timeMax.toISOString(),
        max_results: maxResults.toString(),
        use_cache: useCache.toString(),
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
        latestHype: event.latest_hype
          ? {
              hypeText: event.latest_hype.hype_text,
              audioUrl: event.latest_hype.audio_url,
              managerStyle: event.latest_hype.manager_style,
            }
          : undefined,
        importanceScore: event.importance_score,
        importanceReason: event.importance_reason,
        importanceCategory: event.importance_category,
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

  // Bridge NeedsGoogleAuthError to provider state so the reconnect banner appears
  useEffect(() => {
    if (query.error instanceof NeedsGoogleAuthError) {
      setGoogleAuthNeeded();
    }
  }, [query.error, setGoogleAuthNeeded]);

  return query;
};
