import { Button } from "@/components/ui/button";
import {
  AudioPlayerButton,
  AudioPlayerProgress,
  AudioPlayerTime,
  AudioPlayerDuration,
  AudioPlayerSpeed,
  useAudioPlayer,
} from "@/components/ui/audio-player";
import { BarVisualizer } from "@/components/ui/visualizers";

type AudioPlayerControlsProps = {
  onRegenerate?: () => void;
};

export const AudioPlayerControls = ({ onRegenerate }: AudioPlayerControlsProps) => {
  const { state } = useAudioPlayer();

  return (
    <div className="p-6 bg-gradient-to-b from-white to-gray-50/50">
      <div className="flex items-center gap-4">
        <AudioPlayerButton />

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            <BarVisualizer
              state={state === "playing" ? "playing" : "idle"}
              barCount={24}
              className="flex-1 h-10"
              color="#10b981"
            />
          </div>
          <AudioPlayerProgress />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <AudioPlayerTime />
          <span>/</span>
          <AudioPlayerDuration />
        </div>

        <div className="flex items-center gap-2">
          <AudioPlayerSpeed />
          {onRegenerate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRegenerate}
              className="text-primary-600 hover:bg-primary-50"
            >
              Regenerate
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
