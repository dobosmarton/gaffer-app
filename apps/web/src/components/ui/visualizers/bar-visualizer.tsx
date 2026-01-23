import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { VisualizerState } from "./types";

type BarVisualizerProps = {
  state?: VisualizerState;
  barCount?: number;
  className?: string;
  color?: string;
};

export const BarVisualizer = ({
  state = "idle",
  barCount = 12,
  className,
  color = "#10b981",
}: BarVisualizerProps) => {
  const [bars, setBars] = useState<number[]>(() =>
    Array(barCount).fill(0.2)
  );

  useEffect(() => {
    if (state === "playing") {
      const interval = setInterval(() => {
        setBars(
          Array(barCount)
            .fill(0)
            .map(() => 0.2 + Math.random() * 0.8)
        );
      }, 100);
      return () => clearInterval(interval);
    } else if (state === "loading") {
      const interval = setInterval(() => {
        setBars((prev) => {
          const newBars = [...prev];
          const peakIndex = Math.floor(Date.now() / 150) % barCount;
          return newBars.map((_, i) => {
            const distance = Math.abs(i - peakIndex);
            return Math.max(0.2, 1 - distance * 0.15);
          });
        });
      }, 50);
      return () => clearInterval(interval);
    } else {
      setBars(Array(barCount).fill(0.2));
    }
  }, [state, barCount]);

  return (
    <div
      className={cn(
        "flex items-end justify-center gap-1",
        className
      )}
      style={{ height: 48 }}
    >
      {bars.map((height, index) => (
        <motion.div
          key={index}
          className="w-1 rounded-full"
          style={{ backgroundColor: color }}
          animate={{
            height: `${height * 100}%`,
            opacity: state === "idle" || state === "paused" ? 0.4 : 1,
          }}
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 20,
          }}
        />
      ))}
    </div>
  );
};
