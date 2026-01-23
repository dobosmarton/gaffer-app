import { useMutation } from "@tanstack/react-query";
import { useState, useEffect, useCallback, useRef } from "react";
import type { CalendarEvent, EventHypeState } from "@/components/event-card";

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

export const useHypeGeneration = () => {
  const [hypeStates, setHypeStates] = useState<HypeStatesMap>({});
  const hypeStatesRef = useRef(hypeStates);

  // Keep ref in sync with state
  useEffect(() => {
    hypeStatesRef.current = hypeStates;
  }, [hypeStates]);

  // Clean up blob URLs when component unmounts
  useEffect(() => {
    return () => {
      Object.values(hypeStatesRef.current).forEach((state) => {
        if (state.audioUrl) {
          URL.revokeObjectURL(state.audioUrl);
        }
      });
    };
  }, []);

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
      // Step 1: Generate hype text
      const textResponse = await fetch(`${API_URL}/hype/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_title: event.title,
          event_description: event.description || null,
          event_time: event.start.toISOString(),
          manager_style: manager,
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

      // Step 2: Generate audio
      const audioResponse = await fetch(`${API_URL}/hype/audio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textData.hype_text }),
      });

      if (!audioResponse.ok) {
        const error = await audioResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate audio");
      }

      const audioBlob = await audioResponse.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      return { eventId: event.id, hypeText: textData.hype_text, audioUrl };
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
      const prevState = hypeStates[event.id];
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
    [hypeStates, updateEventState, mutation]
  );

  const getEventHypeState = useCallback(
    (eventId: string): EventHypeState => {
      return hypeStates[eventId] ?? DEFAULT_HYPE_STATE;
    },
    [hypeStates]
  );

  return {
    hypeStates,
    generateHype,
    getEventHypeState,
    isPending: mutation.isPending,
  };
};
