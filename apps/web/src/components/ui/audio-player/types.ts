export type AudioPlayerState = "idle" | "loading" | "playing" | "paused" | "error";

export type AudioPlayerContextType = {
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
