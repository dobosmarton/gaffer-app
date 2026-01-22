import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { EventCard, type CalendarEvent } from "@/components/event-card";
import { HypePlayer } from "@/components/hype-player";
import { ManagerSelector, getManagerName } from "@/components/manager-selector";
import { useCalendarEvents } from "@/hooks/use-calendar-events";
import { useSupabase } from "@/lib/supabase-provider";
import { supabase } from "@/lib/supabase";
import { Calendar, RefreshCw, AlertCircle } from "lucide-react";

export const Route = createFileRoute("/(protected)/dashboard")({
  component: Dashboard,
});

type HypeState = {
  status: "idle" | "generating_text" | "generating_audio" | "ready" | "error";
  eventId: string | null;
  hypeText: string | null;
  audioUrl: string | null;
  manager: string;
};

function Dashboard() {
  const { needsReauth } = useSupabase();
  const [selectedManager, setSelectedManager] = useState("ferguson");
  const [hypeState, setHypeState] = useState<HypeState>({
    status: "idle",
    eventId: null,
    hypeText: null,
    audioUrl: null,
    manager: "ferguson",
  });

  // Fetch real calendar events
  const {
    data: events,
    isLoading,
    error,
    refetch,
    isRefetching
  } = useCalendarEvents({
    maxResults: 10,
  });

  const handleReconnectGoogle = async () => {
    // Re-trigger OAuth flow to get a fresh token
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        scopes: "https://www.googleapis.com/auth/calendar.readonly",
        redirectTo: `${window.location.origin}/dashboard`,
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
  };

  const handleHypeMe = async (event: CalendarEvent) => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    setHypeState({
      status: "generating_text",
      eventId: event.id,
      hypeText: null,
      audioUrl: null,
      manager: selectedManager,
    });

    try {
      // Step 1: Generate hype text with Claude
      const textResponse = await fetch(`${API_URL}/hype/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_title: event.title,
          event_description: event.description || null,
          event_time: event.start.toISOString(),
          manager_style: selectedManager,
        }),
      });

      if (!textResponse.ok) {
        const error = await textResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate hype");
      }

      const textData = await textResponse.json();

      // Show text immediately, start audio generation
      setHypeState((prev) => ({
        ...prev,
        status: "generating_audio",
        hypeText: textData.hype_text,
      }));

      // Step 2: Generate audio with ElevenLabs
      const audioResponse = await fetch(`${API_URL}/hype/audio`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: textData.hype_text,
        }),
      });

      if (!audioResponse.ok) {
        const error = await audioResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate audio");
      }

      // Convert streamed audio to blob URL
      const audioBlob = await audioResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      setHypeState((prev) => ({
        ...prev,
        status: "ready",
        audioUrl,
      }));
    } catch (err) {
      console.error("Failed to generate hype:", err);
      setHypeState((prev) => ({
        ...prev,
        status: "error",
        hypeText: prev.hypeText || (err instanceof Error ? err.message : "Something went wrong"),
      }));
    }
  };

  const handleRegenerate = () => {
    if (hypeState.eventId && events) {
      const event = events.find((e) => e.id === hypeState.eventId);
      if (event) {
        handleHypeMe(event);
      }
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Your Upcoming Meetings</h1>
        <p className="mt-2 text-gray-600">
          Select a meeting and get your pre-match team talk from the gaffer.
        </p>
      </div>

      {/* Manager selector */}
      <ManagerSelector
        selected={selectedManager}
        onSelect={setSelectedManager}
        disabled={hypeState.status === "generating_text" || hypeState.status === "generating_audio"}
      />

      {/* Reconnect banner */}
      {needsReauth && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">Calendar connection expired</p>
              <p className="text-sm text-amber-600">Reconnect to Google to see your meetings</p>
            </div>
          </div>
          <button
            onClick={handleReconnectGoogle}
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 transition-colors"
          >
            Reconnect Google
          </button>
        </div>
      )}

      {/* Events list */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Upcoming Meetings</h2>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {isLoading && (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
            <div className="animate-pulse flex flex-col items-center gap-3">
              <Calendar className="h-8 w-8 text-gray-400" />
              <p className="text-gray-500">Loading your calendar...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-red-700 font-medium">Failed to load calendar events</p>
            <p className="text-red-600 text-sm mt-1">{error.message}</p>
            <button
              onClick={() => refetch()}
              className="mt-4 rounded-lg bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {events && events.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center">
            <Calendar className="h-10 w-10 text-gray-400 mx-auto" />
            <p className="mt-3 text-gray-600 font-medium">No upcoming meetings</p>
            <p className="text-gray-500 text-sm mt-1">
              You're all clear for the next 24 hours!
            </p>
          </div>
        )}

        {events && events.length > 0 && (
          <div className="space-y-3">
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onHypeMe={() => handleHypeMe(event)}
                isGenerating={
                  hypeState.eventId === event.id &&
                  (hypeState.status === "generating_text" ||
                    hypeState.status === "generating_audio")
                }
              />
            ))}
          </div>
        )}
      </div>

      {/* Hype player */}
      {hypeState.status !== "idle" && (
        <div className="pt-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Team Talk</h2>
          <HypePlayer
            hypeText={hypeState.hypeText}
            audioUrl={hypeState.audioUrl}
            status={hypeState.status}
            managerName={getManagerName(hypeState.manager)}
            onRegenerate={handleRegenerate}
          />
        </div>
      )}
    </div>
  );
}
