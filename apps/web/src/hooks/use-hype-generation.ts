import type { CalendarEvent, EventHypeState } from "@/components/event-card";
import { useSupabase } from "@/lib/supabase-provider";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";

export type HypeStatesMap = Record<string, EventHypeState>;

type GenerateHypeParams = {
  event: CalendarEvent;
  manager: string;
};

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const DEFAULT_HYPE_STATE: EventHypeState = {
  status: "idle",
  hypeText: null,
  audioUrl: null,
  manager: "ferguson",
};

export const useHypeGeneration = (events?: CalendarEvent[]) => {
  const { session } = useSupabase();
  const [hypeStates, setHypeStates] = useState<HypeStatesMap>({});

  const mergedHypeStates = useMemo(() => {
    
    if (!events || events.length === 0) return hypeStates;

        const updates = events.reduce<HypeStatesMap>((acc, event) => {
          const existingState = hypeStates[event.id];
          // Only initialize if we don't already have state and event has hype data
          if ((!existingState || existingState.status === "idle") && event.latestHype) {
            acc[event.id] = {
              status: "ready",
              hypeText: event.latestHype.hypeText,
              audioUrl: event.latestHype.audioUrl,
              manager: event.latestHype.managerStyle,
            };
          }
          return acc;
        }, {});

        if (Object.keys(updates).length === 0) return hypeStates;
        return { ...hypeStates, ...updates };

  }, [events, hypeStates]);


  // Clean up blob URLs when component unmounts or state changes
  useEffect(() => {
    return () => {
      Object.values(hypeStates).forEach((state) => {
        if (state.audioUrl) {
          URL.revokeObjectURL(state.audioUrl);
        }
      });
    };
  }, [hypeStates]);

  const updateEventState = useCallback((eventId: string, updates: Partial<EventHypeState>) => {
    setHypeStates((prev) => ({
      ...prev,
      [eventId]: {
        ...(prev[eventId] ?? DEFAULT_HYPE_STATE),
        ...updates,
      },
    }));
  }, []);

  const mutation = useMutation({
    mutationFn: async ({ event, manager }: GenerateHypeParams) => {
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      // Step 1: Generate hype text
      const textResponse = await fetch(`${API_URL}/hype/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          event_title: event.title,
          event_description: event.description || null,
          event_time: event.start.toISOString(),
          manager_style: manager,
          google_event_id: event.id,
          persist: true,
        }),
      });

      if (!textResponse.ok) {
        const error = await textResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate hype");
      }

      const textData = await textResponse.json();

      // Update state with text
      updateEventState(event.id, {
        status: "generating_audio",
        hypeText: textData.hype_text,
      });

      // Step 2: Generate audio (use audio_text which has emotion tags for TTS)
      const audioResponse = await fetch(`${API_URL}/hype/audio`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          text: textData.audio_text,
          manager: manager,
          hype_id: textData.hype_id, // Link audio to hype record
        }),
      });

      if (!audioResponse.ok) {
        const error = await audioResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate audio");
      }

      // Check if audio was persisted (URL in header)
      const persistedAudioUrl = audioResponse.headers.get("X-Audio-Url");

      const audioBlob = await audioResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      return {
        eventId: event.id,
        hypeText: textData.hype_text,
        audioUrl,
        persistedAudioUrl,
        hypeId: textData.hype_id,
      };
    },
    onSuccess: ({ eventId, audioUrl }) => {
      updateEventState(eventId, {
        status: "ready",
        audioUrl,
      });
    },
    onError: (err, { event }) => {
      console.error("Failed to generate hype:", err);
      updateEventState(event.id, {
        status: "error",
      });
    },
  });

  const generateHype = useCallback(
    (event: CalendarEvent, manager: string) => {
      // Clean up previous audio URL if exists
      const prevState = mergedHypeStates[event.id];
      if (prevState?.audioUrl) {
        URL.revokeObjectURL(prevState.audioUrl);
      }

      updateEventState(event.id, {
        status: "generating_text",
        hypeText: null,
        audioUrl: null,
        manager,
      });

      mutation.mutate({ event, manager });
    },
    [mergedHypeStates, updateEventState, mutation]
  );

  const getEventHypeState = useCallback(
    (eventId: string): EventHypeState => {
      return mergedHypeStates[eventId] ?? DEFAULT_HYPE_STATE;
    },
    [mergedHypeStates]
  );

  return {
    hypeStates: mergedHypeStates,
    generateHype,
    getEventHypeState,
    isPending: mutation.isPending,
  };
};
