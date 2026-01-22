import * as Slider from "@radix-ui/react-slider";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Pause, Play, Volume2, VolumeX } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";

type AudioPlayerState = "idle" | "loading" | "playing" | "paused" | "error";

type AudioPlayerContextType = {
  state: AudioPlayerState;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
  audioRef: React.RefObject<HTMLAudioElement | null>;
};

const AudioPlayerContext = createContext<AudioPlayerContextType | null>(null);

export function useAudioPlayer() {
  const context = useContext(AudioPlayerContext);
  if (!context) {
    throw new Error("useAudioPlayer must be used within AudioPlayerProvider");
  }
  return context;
}

type AudioPlayerProviderProps = {
  src: string;
  children: ReactNode;
  onEnded?: () => void;
  onError?: (error: Error) => void;
};

export function AudioPlayerProvider({
  src,
  children,
  onEnded,
  onError,
}: AudioPlayerProviderProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<AudioPlayerState>("idle");
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(1);
  const [playbackRate, setPlaybackRateState] = useState(1);
  const animationRef = useRef<number | null>(null);

  const updateTime = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
    animationRef.current = requestAnimationFrame(updateTime);
  }, []);

  useEffect(() => {
    const audio = new Audio(src);
    audioRef.current = audio;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setState("idle");
    };

    const handlePlay = () => {
      setState("playing");
      animationRef.current = requestAnimationFrame(updateTime);
    };

    const handlePause = () => {
      setState("paused");
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };

    const handleEnded = () => {
      setState("idle");
      setCurrentTime(0);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      onEnded?.();
    };

    const handleError = () => {
      setState("error");
      onError?.(new Error("Failed to load audio"));
    };

    const handleWaiting = () => {
      setState("loading");
    };

    const handleCanPlay = () => {
      setState((prev) => (prev === "loading" ? "idle" : prev));
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);
    audio.addEventListener("waiting", handleWaiting);
    audio.addEventListener("canplay", handleCanPlay);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
      audio.removeEventListener("waiting", handleWaiting);
      audio.removeEventListener("canplay", handleCanPlay);
      audio.pause();
      audio.src = "";
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [src, onEnded, onError, updateTime]);

  const play = useCallback(() => {
    audioRef.current?.play();
  }, []);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const toggle = useCallback(() => {
    if (state === "playing") {
      pause();
    } else {
      play();
    }
  }, [state, play, pause]);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  const setVolume = useCallback((newVolume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
      setVolumeState(newVolume);
    }
  }, []);

  const setPlaybackRate = useCallback((rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlaybackRateState(rate);
    }
  }, []);

  return (
    <AudioPlayerContext.Provider
      value={{
        state,
        currentTime,
        duration,
        volume,
        playbackRate,
        play,
        pause,
        toggle,
        seek,
        setVolume,
        setPlaybackRate,
        audioRef,
      }}
    >
      {children}
    </AudioPlayerContext.Provider>
  );
}

export function AudioPlayerButton({ className }: { className?: string }) {
  const { state, toggle } = useAudioPlayer();

  return (
    <button
      onClick={toggle}
      disabled={state === "loading" || state === "error"}
      className={cn(
        "flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-teal-500 text-white shadow-lg shadow-primary-500/25 transition-all hover:shadow-xl hover:shadow-primary-500/30 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed",
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
    </button>
  );
}

export function AudioPlayerProgress({ className }: { className?: string }) {
  const { currentTime, duration, seek, state } = useAudioPlayer();
  const [isSeeking, setIsSeeking] = useState(false);
  const [seekValue, setSeekValue] = useState(0);

  const displayTime = isSeeking ? seekValue : currentTime;
  const progress = duration > 0 ? (displayTime / duration) * 100 : 0;

  return (
    <Slider.Root
      className={cn(
        "relative flex h-5 w-full touch-none select-none items-center",
        className
      )}
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
    >
      <Slider.Track className="relative h-2 grow rounded-full bg-gradient-to-r from-gray-100 to-gray-200">
        <Slider.Range className="absolute h-full rounded-full bg-gradient-to-r from-primary-500 to-teal-500" />
      </Slider.Track>
      <Slider.Thumb
        className="block h-4 w-4 rounded-full bg-gradient-to-br from-primary-500 to-teal-500 shadow-md shadow-primary-500/25 transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:ring-offset-2"
        aria-label="Playback position"
      />
    </Slider.Root>
  );
}

export function AudioPlayerTime({ className }: { className?: string }) {
  const { currentTime } = useAudioPlayer();
  return (
    <span className={cn("text-sm tabular-nums text-gray-600", className)}>
      {formatTime(currentTime)}
    </span>
  );
}

export function AudioPlayerDuration({ className }: { className?: string }) {
  const { duration } = useAudioPlayer();
  return (
    <span className={cn("text-sm tabular-nums text-gray-600", className)}>
      {formatTime(duration)}
    </span>
  );
}

export function AudioPlayerVolume({ className }: { className?: string }) {
  const { volume, setVolume } = useAudioPlayer();

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <button
        onClick={() => setVolume(volume > 0 ? 0 : 1)}
        className="text-gray-600 hover:text-gray-900"
      >
        {volume > 0 ? (
          <Volume2 className="h-4 w-4" />
        ) : (
          <VolumeX className="h-4 w-4" />
        )}
      </button>
      <Slider.Root
        className="relative flex h-5 w-20 touch-none select-none items-center"
        value={[volume]}
        max={1}
        step={0.01}
        onValueChange={([value]) => setVolume(value ?? 0)}
      >
        <Slider.Track className="relative h-1 grow rounded-full bg-gray-200">
          <Slider.Range className="absolute h-full rounded-full bg-gray-400" />
        </Slider.Track>
        <Slider.Thumb
          className="block h-3 w-3 rounded-full bg-gray-600 shadow-sm focus:outline-none"
          aria-label="Volume"
        />
      </Slider.Root>
    </div>
  );
}

export function AudioPlayerSpeed({ className }: { className?: string }) {
  const { playbackRate, setPlaybackRate } = useAudioPlayer();
  const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          className={cn(
            "rounded px-2 py-1 text-sm font-medium text-gray-600 hover:bg-gray-100",
            className
          )}
        >
          {playbackRate === 1 ? "1x" : `${playbackRate}x`}
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="z-50 min-w-[80px] rounded-md bg-white p-1 shadow-lg ring-1 ring-black/5"
          sideOffset={5}
        >
          {speeds.map((speed) => (
            <DropdownMenu.Item
              key={speed}
              className={cn(
                "cursor-pointer rounded px-3 py-1.5 text-sm outline-none hover:bg-gray-100",
                playbackRate === speed && "bg-gray-100 font-medium"
              )}
              onSelect={() => setPlaybackRate(speed)}
            >
              {speed === 1 ? "Normal" : `${speed}x`}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
