import { motion, useInView } from "motion/react";
import { useRef } from "react";
import { cn } from "@/lib/utils";

type ShimmeringTextProps = {
  text: string;
  className?: string;
  duration?: number;
  repeat?: boolean;
  startOnView?: boolean;
  shimmerColor?: string;
};

export const ShimmeringText = ({
  text,
  className,
  duration = 2,
  repeat = true,
  startOnView = true,
  shimmerColor = "rgba(255, 255, 255, 0.8)",
}: ShimmeringTextProps) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: !repeat });

  const shouldAnimate = startOnView ? isInView : true;

  return (
    <motion.span
      ref={ref}
      className={cn(
        "relative inline-block bg-clip-text text-transparent",
        className
      )}
      style={{
        backgroundImage: `linear-gradient(
          90deg,
          currentColor 0%,
          currentColor 40%,
          ${shimmerColor} 50%,
          currentColor 60%,
          currentColor 100%
        )`,
        backgroundSize: "200% 100%",
        WebkitBackgroundClip: "text",
      }}
      animate={
        shouldAnimate
          ? {
              backgroundPosition: ["100% 0%", "-100% 0%"],
            }
          : undefined
      }
      transition={{
        duration,
        repeat: repeat ? Infinity : 0,
        ease: "linear",
      }}
    >
      {text}
    </motion.span>
  );
};
