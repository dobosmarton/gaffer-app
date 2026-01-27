import { useState, useRef } from "react";
import { Play, Pause } from "lucide-react";
import { Waveform } from "./waveform";

export type Manager = {
  id: string;
  name: string;
  style: string;
};

export function ManagerCard({ manager }: { manager: Manager }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleEnded = () => setIsPlaying(false);

  return (
    <div className="relative rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm overflow-hidden">
      <Waveform isPlaying={isPlaying} />
      <div className="relative flex items-center z-10">
        <button
          onClick={togglePlay}
          className="flex-shrink-0 flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25 transition-all hover:scale-105"
          aria-label={isPlaying ? "Pause" : `Play ${manager.name} sample`}
        >
          {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-0.5" />}
        </button>
        <div className="ml-4 text-left">
          <p className="font-semibold text-white">{manager.name}</p>
          <p className="text-sm text-slate-400">{manager.style}</p>
        </div>
      </div>
      <audio
        ref={audioRef}
        src={`/samples/${manager.id}-intro.mp3`}
        onEnded={handleEnded}
        preload="none"
      />
    </div>
  );
}
