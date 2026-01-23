import { cn } from "@/lib/utils";
import { useAudioPlayer } from "./audio-player-context";
import { formatTime } from "./utils";

type AudioPlayerDurationProps = {
  className?: string;
};

export const AudioPlayerDuration = ({ className }: AudioPlayerDurationProps) => {
  const { duration } = useAudioPlayer();
  return (
    <span className={cn("text-sm tabular-nums text-gray-600", className)}>
      {formatTime(duration)}
    </span>
  );
};
