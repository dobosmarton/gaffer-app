import { useSupabase } from "@/lib/supabase-provider";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type InterestStatus = {
  registered: boolean;
  registered_at: string | null;
};

export const useUpgradeInterest = () => {
  const { session } = useSupabase();
  const queryClient = useQueryClient();

  const statusQuery = useQuery<InterestStatus, Error>({
    queryKey: ["upgrade-interest", session?.user?.id],
    queryFn: async () => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_URL}/hype/interest/status`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail?.message || error.detail || "Failed to fetch interest status");
      }

      return response.json();
    },
    enabled: !!session?.access_token,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const registerMutation = useMutation<InterestStatus, Error, void>({
    mutationFn: async () => {
      if (!session?.access_token || !session?.user?.email) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_URL}/hype/interest`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: session.user.email }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail?.message || error.detail || "Failed to register interest");
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upgrade-interest"] });
    },
  });

  return {
    status: statusQuery.data,
    isLoading: statusQuery.isLoading,
    isRegistered: statusQuery.data?.registered ?? false,
    registerInterest: registerMutation.mutate,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,
  };
};
