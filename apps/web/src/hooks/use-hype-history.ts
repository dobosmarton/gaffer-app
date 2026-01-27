import { useSupabase } from "@/lib/supabase-provider";
import { useQuery } from "@tanstack/react-query";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type HypeHistoryItem = {
  id: string;
  event_title: string;
  event_time: string;
  manager_style: string;
  hype_text: string | null;
  audio_url: string | null;
  status: string;
  created_at: string;
};

type HypeHistoryResponse = {
  records: HypeHistoryItem[];
};

export const useHypeHistory = (options?: {
  googleEventId?: string;
  limit?: number;
  enabled?: boolean;
}) => {
  const { session } = useSupabase();

  return useQuery<HypeHistoryItem[], Error>({
    queryKey: ["hype-history", session?.user?.id, options?.googleEventId],
    queryFn: async () => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const params = new URLSearchParams();
      if (options?.googleEventId) {
        params.set("google_event_id", options.googleEventId);
      }
      if (options?.limit) {
        params.set("limit", options.limit.toString());
      }

      const response = await fetch(`${API_URL}/hype/history?${params}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to fetch hype history");
      }

      const data: HypeHistoryResponse = await response.json();
      return data.records;
    },
    enabled: (options?.enabled ?? true) && !!session?.access_token,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
};

export const useEventHypeHistory = (
  googleEventId: string,
  options?: {
    limit?: number;
    enabled?: boolean;
  }
) => {
  return useHypeHistory({
    googleEventId,
    limit: options?.limit ?? 5,
    enabled: options?.enabled ?? true,
  });
};
