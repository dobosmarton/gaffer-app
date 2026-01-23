import { useState } from "react";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import { useAudioPlayer } from "./audio-player-context";

type AudioPlayerProgressProps = {
  className?: string;
};

export const AudioPlayerProgress = ({ className }: AudioPlayerProgressProps) => {
  const { currentTime, duration, seek, state } = useAudioPlayer();
  const [isSeeking, setIsSeeking] = useState(false);
  const [seekValue, setSeekValue] = useState(0);

  const displayTime = isSeeking ? seekValue : currentTime;

  return (
    <Slider
      className={cn("w-full", className)}
      value={[displayTime]}
      max={duration || 100}
      step={0.1}
      onValueChange={([value]) => {
        setIsSeeking(true);
        setSeekValue(value ?? 0);
      }}
      onValueCommit={([value]) => {
        seek(value ?? 0);
        setIsSeeking(false);
      }}
      disabled={state === "loading" || state === "error"}
    />
  );
};
