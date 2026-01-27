import { cn } from "@/lib/utils";
import { useAudioPlayer } from "./audio-player-context";
import { formatTime } from "./utils";

type AudioPlayerTimeProps = {
  className?: string;
};

export const AudioPlayerTime = ({ className }: AudioPlayerTimeProps) => {
  const { currentTime } = useAudioPlayer();
  return (
    <span className={cn("text-sm tabular-nums text-muted-foreground", className)}>
      {formatTime(currentTime)}
    </span>
  );
};
