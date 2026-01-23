import { useMutation } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import type { CalendarEvent } from "@/components/event-card";

export type HypeState = {
  status: "idle" | "generating_text" | "generating_audio" | "ready" | "error";
  eventId: string | null;
  hypeText: string | null;
  audioUrl: string | null;
  manager: string;
};

type UseHypeGenerationOptions = {
  selectedManager: string;
};

type GenerateHypeParams = {
  event: CalendarEvent;
  manager: string;
};

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const useHypeGeneration = ({ selectedManager }: UseHypeGenerationOptions) => {
  const [hypeState, setHypeState] = useState<HypeState>({
    status: "idle",
    eventId: null,
    hypeText: null,
    audioUrl: null,
    manager: "ferguson",
  });

  // Clean up blob URLs to prevent memory leaks
  useEffect(() => {
    return () => {
      if (hypeState.audioUrl) {
        URL.revokeObjectURL(hypeState.audioUrl);
      }
    };
  }, [hypeState.audioUrl]);

  const mutation = useMutation({
    mutationFn: async ({ event, manager }: GenerateHypeParams) => {
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
          manager_style: manager,
        }),
      });

      if (!textResponse.ok) {
        const error = await textResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to generate hype");
      }

      const textData = await textResponse.json();

      // Update state with text, start audio generation
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

      return { hypeText: textData.hype_text, audioUrl };
    },
    onSuccess: ({ audioUrl }) => {
      setHypeState((prev) => ({
        ...prev,
        status: "ready",
        audioUrl,
      }));
    },
    onError: (err) => {
      console.error("Failed to generate hype:", err);
      setHypeState((prev) => ({
        ...prev,
        status: "error",
        hypeText: prev.hypeText || (err instanceof Error ? err.message : "Something went wrong"),
      }));
    },
  });

  const generateHype = (event: CalendarEvent) => {
    setHypeState({
      status: "generating_text",
      eventId: event.id,
      hypeText: null,
      audioUrl: null,
      manager: selectedManager,
    });

    mutation.mutate({ event, manager: selectedManager });
  };

  const regenerate = (events: CalendarEvent[] | undefined) => {
    if (hypeState.eventId && events) {
      const event = events.find((e) => e.id === hypeState.eventId);
      if (event) {
        generateHype(event);
      }
    }
  };

  return {
    hypeState,
    generateHype,
    regenerate,
    isPending: mutation.isPending,
  };
};
