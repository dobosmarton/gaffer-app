import { EventsList } from "@/components/events-list";
import { GoogleReconnectBanner } from "@/components/google-reconnect-banner";
import { Card } from "@/components/ui/card";
import { useCalendarEvents, useCalendarSync } from "@/hooks/use-calendar-events";
import { useHypeGeneration } from "@/hooks/use-hype-generation";
import { useUsage, type UsageInfo } from "@/hooks/use-usage";
import { useSupabase } from "@/lib/supabase-provider";
import { createFileRoute } from "@tanstack/react-router";
import { Megaphone } from "lucide-react";
import { useEffect } from "react";

export const Route = createFileRoute("/(protected)/dashboard")({
  component: Dashboard,
});

const UsageCard = ({ usage }: { usage: UsageInfo | undefined }) => {
  if (!usage) {
    return (
      <Card className="p-5 animate-pulse">
        <div className="h-4 w-32 bg-gray-200 rounded mb-3" />
        <div className="h-2 w-full bg-gray-100 rounded mb-2" />
        <div className="h-3 w-24 bg-gray-100 rounded" />
      </Card>
    );
  }

  const percentage = (usage.used / usage.limit) * 100;
  const remaining = usage.limit - usage.used;
  const isAtLimit = remaining === 0;
  const isNearLimit = percentage >= 80 && !isAtLimit;

  const resetDate = new Date(usage.resets_at);
  const daysUntilReset = Math.ceil(
    (resetDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500">
              <Megaphone className="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Monthly Speeches</h3>
              <p className="text-xs text-gray-500 capitalize">{usage.plan} plan</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mb-2">
            <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  isAtLimit
                    ? "bg-red-500"
                    : isNearLimit
                      ? "bg-amber-500"
                      : "bg-gradient-to-r from-amber-500 to-orange-500"
                }`}
                style={{ width: `${Math.min(percentage, 100)}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className={isAtLimit ? "text-red-600 font-medium" : "text-gray-600"}>
              {usage.used} of {usage.limit} used
            </span>
            <span className="text-gray-500">
              Resets in {daysUntilReset} day{daysUntilReset !== 1 ? "s" : ""}
            </span>
          </div>

          {isAtLimit && (
            <p className="mt-3 text-sm text-red-600">
              You've reached your monthly limit. Upgrade for more speeches.
            </p>
          )}
        </div>
      </div>
    </Card>
  );
};

function Dashboard() {
  const { needsGoogleAuth, reconnectGoogle } = useSupabase();

  const { data: events, isLoading, error, isRefetching } = useCalendarEvents({ maxResults: 10 });

  // Pass events to load existing hype records
  const { generateHype, getEventHypeState } = useHypeGeneration(events);

  const { usage } = useUsage();
  const canGenerate = !!usage?.can_generate;

  const syncMutation = useCalendarSync();

  // Sync calendar on mount (if not recently synced)
  useEffect(() => {
    if (!needsGoogleAuth && !syncMutation.isPending) {
      syncMutation.mutate({});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needsGoogleAuth]);

  const handleRefetch = async () => {
    // Trigger sync first, then refetch (sync already invalidates the query)
    await syncMutation.mutateAsync({});
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Upcoming Meetings</h1>
          <p className="mt-1 text-gray-600">Select a meeting and get your pre-match team talk.</p>
        </div>
        <div className="w-80 flex-shrink-0">
          <UsageCard usage={usage} />
        </div>
      </div>

      {needsGoogleAuth && <GoogleReconnectBanner onReconnect={reconnectGoogle} />}

      <EventsList
        events={events}
        isLoading={isLoading}
        error={error}
        getEventHypeState={getEventHypeState}
        onGenerateHype={generateHype}
        onRefetch={handleRefetch}
        isRefetching={isRefetching || syncMutation.isPending}
        canGenerate={canGenerate}
      />
    </div>
  );
}
