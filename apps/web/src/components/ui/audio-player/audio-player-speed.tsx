import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useAudioPlayer } from "./audio-player-context";

type AudioPlayerSpeedProps = {
  className?: string;
};

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

export const AudioPlayerSpeed = ({ className }: AudioPlayerSpeedProps) => {
  const { playbackRate, setPlaybackRate } = useAudioPlayer();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn("text-gray-600 hover:bg-gray-100", className)}
        >
          {playbackRate === 1 ? "1x" : `${playbackRate}x`}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {SPEEDS.map((speed) => (
          <DropdownMenuItem
            key={speed}
            onClick={() => setPlaybackRate(speed)}
            className={cn(playbackRate === speed && "bg-gray-100 font-medium")}
          >
            {speed === 1 ? "Normal" : `${speed}x`}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
