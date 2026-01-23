import { Pause, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAudioPlayer } from "./audio-player-context";

type AudioPlayerButtonProps = {
  className?: string;
};

export const AudioPlayerButton = ({ className }: AudioPlayerButtonProps) => {
  const { state, toggle } = useAudioPlayer();

  return (
    <Button
      onClick={toggle}
      disabled={state === "loading" || state === "error"}
      className={cn(
        "h-14 w-14 rounded-full bg-gradient-to-br from-primary-500 to-teal-500 text-white shadow-lg shadow-primary-500/25 transition-all hover:shadow-xl hover:shadow-primary-500/30 hover:scale-105",
        state === "loading" && "animate-pulse",
        className
      )}
      aria-label={state === "playing" ? "Pause" : "Play"}
    >
      {state === "playing" ? (
        <Pause className="h-6 w-6 fill-current" />
      ) : (
        <Play className="h-6 w-6 fill-current ml-0.5" />
      )}
    </Button>
  );
};
