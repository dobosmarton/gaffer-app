import { createFileRoute } from "@tanstack/react-router";
import { EventsList } from "@/components/events-list";
import { GoogleReconnectBanner } from "@/components/google-reconnect-banner";
import { useCalendarEvents } from "@/hooks/use-calendar-events";
import { useHypeGeneration } from "@/hooks/use-hype-generation";
import { useSupabase } from "@/lib/supabase-provider";

export const Route = createFileRoute("/(protected)/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const { needsGoogleAuth, reconnectGoogle } = useSupabase();

  const {
    data: events,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useCalendarEvents({ maxResults: 10 });

  const { generateHype, getEventHypeState } = useHypeGeneration();

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
        onRefetch={refetch}
        isRefetching={isRefetching}
      />
    </div>
  );
}
