import { useQuery } from "@tanstack/react-query";
import { useSupabase } from "@/lib/supabase-provider";
import { fetchCalendarEvents } from "@/lib/google-calendar";
import type { CalendarEvent } from "@/components/event-card";

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
      return fetchCalendarEvents(googleAccessToken, options);
    },
    enabled: !!googleAccessToken,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });
}
