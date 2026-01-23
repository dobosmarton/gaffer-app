import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { EventsList } from "@/components/events-list";
import { GoogleReconnectBanner } from "@/components/google-reconnect-banner";
import { TeamTalkSection } from "@/components/team-talk-section";
import { ManagerSelector, getManagerName } from "@/components/manager-selector";
import { useCalendarEvents } from "@/hooks/use-calendar-events";
import { useHypeGeneration } from "@/hooks/use-hype-generation";
import { useSupabase } from "@/lib/supabase-provider";

export const Route = createFileRoute("/(protected)/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const { needsGoogleAuth, reconnectGoogle } = useSupabase();
  const [selectedManager, setSelectedManager] = useState("ferguson");

  const {
    data: events,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useCalendarEvents({ maxResults: 10 });

  const { hypeState, generateHype, regenerate } = useHypeGeneration({
    selectedManager,
  });

  const isGenerating =
    hypeState.status === "generating_text" || hypeState.status === "generating_audio";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Your Upcoming Meetings</h1>
        <p className="mt-2 text-gray-600">
          Select a meeting and get your pre-match team talk from the gaffer.
        </p>
      </div>

      <ManagerSelector
        selected={selectedManager}
        onSelect={setSelectedManager}
        disabled={isGenerating}
      />

      {needsGoogleAuth && <GoogleReconnectBanner onReconnect={reconnectGoogle} />}

      <EventsList
        events={events}
        isLoading={isLoading}
        error={error}
        hypeState={hypeState}
        onHypeMe={generateHype}
        onRefetch={refetch}
        isRefetching={isRefetching}
      />

      <TeamTalkSection
        hypeState={hypeState}
        managerName={getManagerName(hypeState.manager)}
        onRegenerate={() => regenerate(events)}
      />
    </div>
  );
};
