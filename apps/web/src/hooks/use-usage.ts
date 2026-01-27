import { useSupabase } from "@/lib/supabase-provider";
import { useQuery } from "@tanstack/react-query";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type UsageInfo = {
  used: number;
  limit: number;
  plan: string;
  resets_at: string;
  can_generate: boolean;
};

export class UsageLimitError extends Error {
  used: number;
  limit: number;
  resetsAt: string;

  constructor(detail: { message: string; used: number; limit: number; resets_at: string }) {
    super(detail.message);
    this.name = "UsageLimitError";
    this.used = detail.used;
    this.limit = detail.limit;
    this.resetsAt = detail.resets_at;
  }
}

export const useUsage = () => {
  const { session } = useSupabase();

  const query = useQuery<UsageInfo, Error>({
    queryKey: ["usage", session?.user?.id],
    queryFn: async () => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_URL}/hype/usage`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail?.message || error.detail || "Failed to fetch usage");
      }

      return response.json();
    },
    enabled: !!session?.access_token,
    staleTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 60 * 5, // Refetch every 5 minutes
  });

  return {
    ...query,
    usage: query.data,
  };
};
