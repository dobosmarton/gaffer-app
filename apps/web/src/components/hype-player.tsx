import { motion, AnimatePresence } from "motion/react";
import {
  AudioPlayerProvider,
  AudioPlayerButton,
  AudioPlayerProgress,
  AudioPlayerTime,
  AudioPlayerDuration,
  AudioPlayerSpeed,
  useAudioPlayer,
} from "@/components/ui/audio-player";
import { BarVisualizer } from "@/components/ui/bar-visualizer";
import { ShimmeringText } from "@/components/ui/shimmering-text";
import { cn } from "@/lib/utils";

type HypeStatus = "idle" | "generating_text" | "generating_audio" | "ready" | "error";

type HypePlayerProps = {
  hypeText: string | null;
  audioUrl: string | null;
  status: HypeStatus;
  managerName: string;
  onRegenerate?: () => void;
  className?: string;
};

export function HypePlayer({
  hypeText,
  audioUrl,
  status,
  managerName,
  onRegenerate,
  className,
}: HypePlayerProps) {
  const isGenerating = status === "generating_text" || status === "generating_audio";
  const hasAudio = status === "ready" && audioUrl;

  return (
    <div className={cn("rounded-2xl bg-white shadow-xl overflow-hidden border border-gray-100", className)}>
      {/* Header */}
      <div className="relative bg-pitch-dark px-6 py-5 overflow-hidden">
        {/* Decorative gradient blurs */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-20 -right-20 h-40 w-40 rounded-full bg-primary-500/20 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-40 w-40 rounded-full bg-teal-500/20 blur-3xl" />
        </div>

        {/* Status indicator */}
        <div className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-xl">
            {isGenerating ? "⏳" : status === "ready" ? "🎙️" : "⚽"}
          </div>

          <AnimatePresence mode="wait">
            {status === "generating_text" && (
              <motion.div
                key="generating-text"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
              >
                <ShimmeringText
                  text="The gaffer is preparing your talk..."
                  className="text-base font-medium text-primary-200"
                  shimmerColor="rgba(45, 212, 191, 0.8)"
                />
              </motion.div>
            )}
            {status === "generating_audio" && (
              <motion.div
                key="generating-audio"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
              >
                <ShimmeringText
                  text="Recording the team talk..."
                  className="text-base font-medium text-primary-200"
                  shimmerColor="rgba(45, 212, 191, 0.8)"
                />
              </motion.div>
            )}
            {status === "ready" && (
              <motion.p
                key="ready"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="text-base font-medium text-primary-200"
              >
                {managerName} has a message for you
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Hype text display */}
      <AnimatePresence>
        {hypeText && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-b border-gray-100"
          >
            <div className="p-6">
              <p className="text-lg italic text-gray-700 leading-relaxed">
                "{hypeText}"
              </p>
              <p className="mt-3 text-sm font-medium text-gray-500">
                — {managerName}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Audio player */}
      <AnimatePresence>
        {hasAudio && audioUrl && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <AudioPlayerProvider src={audioUrl}>
              <AudioPlayerControls onRegenerate={onRegenerate} />
            </AudioPlayerProvider>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading state for audio */}
      {status === "generating_audio" && hypeText && (
        <div className="p-6 border-t border-gray-100 bg-gradient-to-r from-primary-50/50 to-teal-50/50">
          <div className="flex items-center justify-center gap-4">
            <BarVisualizer state="loading" barCount={8} className="h-8" color="#10b981" />
            <span className="text-sm text-primary-700">Generating audio...</span>
          </div>
        </div>
      )}
    </div>
  );
}

function AudioPlayerControls({ onRegenerate }: { onRegenerate?: () => void }) {
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
            <button
              onClick={onRegenerate}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50 transition-colors"
            >
              Regenerate
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
