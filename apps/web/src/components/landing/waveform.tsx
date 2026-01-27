export function Waveform({ isPlaying }: { isPlaying: boolean }) {
  const bars = [0.4, 0.7, 0.5, 0.9, 0.6, 1, 0.5, 0.8, 0.4, 0.7, 0.55, 0.95, 0.5, 0.8, 0.45, 0.75, 0.55, 0.85, 0.6, 0.9, 0.5, 0.85];
  const totalBars = bars.length;

  return (
    <div className="absolute -right-12 top-1/2 -translate-y-1/2 flex items-center gap-[4px] pointer-events-none pr-4">
      {bars.map((height, i) => {
        // Fade out towards the right (last bars get lower opacity)
        const fadeStart = totalBars * 0.4;
        const opacity = i < fadeStart ? 0.1 : 0.1 * (1 - (i - fadeStart) / (totalBars - fadeStart));

        return (
          <div
            key={i}
            className="w-[4px] rounded-full"
            style={{
              height: `${height * 64}px`,
              backgroundColor: `rgba(245, 158, 11, ${opacity})`,
              animation: isPlaying ? `wavebar 0.8s ease-in-out infinite` : undefined,
              animationDelay: isPlaying ? `${i * 0.05}s` : undefined,
            }}
          />
        );
      })}
      <style>{`
        @keyframes wavebar {
          0%, 100% { transform: scaleY(1); }
          50% { transform: scaleY(0.5); }
        }
      `}</style>
    </div>
  );
}
