import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";

type ImportanceBadgeProps = {
  score: number | null | undefined;
  reason?: string | null;
  category?: string | null;
  className?: string;
};

export const ImportanceBadge = ({
  score,
  reason,
  category,
  className,
}: ImportanceBadgeProps) => {
  if (score === null || score === undefined) {
    return null;
  }

  const flames = getFlameCount(score);
  const { color, bgColor } = getScoreColors(score);

  if (flames === 0) {
    return null;
  }

  const tooltipText = `${reason || getCategoryLabel(category)} (Priority: ${score}/10)`;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-0.5 px-2 py-1 rounded-full text-xs font-medium cursor-help",
        bgColor,
        className
      )}
      title={tooltipText}
    >
      {Array.from({ length: flames }).map((_, i) => (
        <Flame
          key={i}
          className={cn("h-3.5 w-3.5", color)}
          fill="currentColor"
        />
      ))}
      {score >= 7 && (
        <span className={cn("ml-1", color)}>Important</span>
      )}
    </div>
  );
};

const getFlameCount = (score: number): number => {
  if (score >= 8) return 3;
  if (score >= 6) return 2;
  if (score >= 4) return 1;
  return 0;
};

const getScoreColors = (score: number): { color: string; bgColor: string } => {
  if (score >= 8) {
    return {
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    };
  }
  if (score >= 6) {
    return {
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
    };
  }
  if (score >= 4) {
    return {
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
    };
  }
  return {
    color: "text-gray-400",
    bgColor: "bg-gray-400/10",
  };
};

const getCategoryLabel = (category: string | null | undefined): string => {
  switch (category) {
    case "high_stakes":
      return "High-stakes meeting - get hyped!";
    case "moderate":
      return "Worth preparing for";
    case "routine":
      return "Routine meeting";
    default:
      return "Meeting importance analyzed";
  }
};
