import { useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { EventsList } from "@/components/events-list";
import { GoogleReconnectBanner } from "@/components/google-reconnect-banner";
import { useCalendarEvents, useCalendarSync } from "@/hooks/use-calendar-events";
import { useHypeGeneration } from "@/hooks/use-hype-generation";
import { useSupabase } from "@/lib/supabase-provider";

export const Route = createFileRoute("/(protected)/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const { needsGoogleAuth, reconnectGoogle } = useSupabase();

  const { data: events, isLoading, error, isRefetching } = useCalendarEvents({ maxResults: 10 });

  // Pass events to load existing hype records
  const { generateHype, getEventHypeState } = useHypeGeneration(events);

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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Your Upcoming Meetings</h1>
        <p className="mt-1 text-gray-600">Select a meeting and get your pre-match team talk.</p>
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
      />
    </div>
  );
}
