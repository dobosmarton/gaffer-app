import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Check, Clock, Loader2, MapPin, RefreshCw, Sparkles, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AudioPlayerProvider,
  AudioPlayerButton,
  AudioPlayerProgress,
  AudioPlayerTime,
  AudioPlayerDuration,
  AudioPlayerSpeed,
} from "@/components/ui/audio-player";
import { cn } from "@/lib/utils";
import { getManagerName } from "@/components/manager-selector";
import { ManagerDropdown } from "@/components/manager-dropdown";
import { ImportanceBadge } from "@/components/importance-badge";

export type LatestHype = {
  hypeText: string | null;
  audioUrl: string | null;
  managerStyle: string;
};

export type CalendarEvent = {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  location?: string;
  attendees?: number;
  latestHype?: LatestHype;
  // Importance scoring fields
  importanceScore?: number | null;
  importanceReason?: string | null;
  importanceCategory?: string | null;
};

export type EventHypeState = {
  status: "idle" | "generating_text" | "generating_audio" | "ready" | "error";
  hypeText: string | null;
  audioUrl: string | null;
  manager: string;
  errorMessage?: string;
};

type EventCardProps = {
  event: CalendarEvent;
  hypeState: EventHypeState;
  onGenerateHype: (managerId: string) => void;
  className?: string;
  canGenerate?: boolean;
  isInterestRegistered?: boolean;
  isRegisteringInterest?: boolean;
  onRegisterInterest?: () => void;
};

export const EventCard = ({
  event,
  hypeState,
  onGenerateHype,
  className,
  canGenerate = true,
  isInterestRegistered = false,
  isRegisteringInterest = false,
  onRegisterInterest,
}: EventCardProps) => {
  // Use manager from hype state if available, otherwise default to ferguson
  // The hype state manager is set when data is loaded from the backend
  const [selectedManager, setSelectedManager] = useState(hypeState.manager || "ferguson");

  const timeUntil = getTimeUntil(event.start);
  const isStartingSoon = timeUntil.minutes < 30 && timeUntil.hours === 0;
  const isGenerating =
    hypeState.status === "generating_text" || hypeState.status === "generating_audio";
  const hasContent = hypeState.status !== "idle";
  const isHighImportance = event.importanceScore !== null && event.importanceScore !== undefined && event.importanceScore >= 7;

  return (
    <Card
      className={cn(
        "overflow-hidden transition-shadow hover:shadow-md",
        isStartingSoon && "border-orange-500/50 dark:border-orange-500/30",
        isHighImportance && !isStartingSoon && "border-amber-500/30 dark:border-amber-500/20 bg-amber-500/5",
        className
      )}
    >
      {/* Main event info */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground truncate">{event.title}</h3>
              <ImportanceBadge
                score={event.importanceScore}
                reason={event.importanceReason}
                category={event.importanceCategory}
              />
            </div>

            {event.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{event.description}</p>
            )}

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span>
                  {formatTime(event.start)} - {formatTime(event.end)}
                </span>
              </div>

              {event.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate max-w-[150px]">{event.location}</span>
                </div>
              )}

              {event.attendees && event.attendees > 1 && (
                <div className="flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span>{event.attendees} attendees</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <Badge
              variant={isStartingSoon ? "destructive" : "secondary"}
              className={cn(
                "rounded-full cursor-default",
                isStartingSoon
                  ? "bg-transparent text-orange-500 border border-orange-500/50 hover:bg-transparent"
                  : "bg-secondary text-muted-foreground hover:bg-secondary"
              )}
            >
              {formatTimeUntil(timeUntil)}
            </Badge>

            {/* Manager selector + Hype button */}
            <div className="flex items-center gap-2">
              <ManagerDropdown
                selected={selectedManager}
                onSelect={setSelectedManager}
                disabled={isGenerating || !canGenerate}
              />

              {!canGenerate && onRegisterInterest ? (
                isInterestRegistered ? (
                  <div className="flex items-center gap-1.5 text-xs text-amber-500 border border-amber-500/30 px-3 py-2 rounded-lg">
                    <Check className="h-3.5 w-3.5" />
                    <span>Notified</span>
                  </div>
                ) : (
                  <Button
                    onClick={onRegisterInterest}
                    disabled={isRegisteringInterest}
                    size="sm"
                    className="shadow-md bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600"
                  >
                    {isRegisteringInterest ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        <span className="hidden sm:inline ml-1">Want more?</span>
                      </>
                    )}
                  </Button>
                )
              ) : (
                <Button
                  onClick={() => onGenerateHype(selectedManager)}
                  disabled={isGenerating || !canGenerate}
                  size="sm"
                  className={cn(
                    "shadow-md",
                    canGenerate
                      ? "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600"
                      : "bg-muted cursor-not-allowed"
                  )}
                  title={!canGenerate ? "Monthly limit reached" : undefined}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="hidden sm:inline ml-1">Generating...</span>
                    </>
                  ) : !canGenerate ? (
                    "Limit Reached"
                  ) : (
                    "Hype Me"
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expandable hype content */}
      <AnimatePresence>
        {hasContent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="border-t border-border bg-secondary/50">
              {/* Generating text state */}
              {hypeState.status === "generating_text" && (
                <div className="p-6 flex items-center justify-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-amber-500" />
                  <span className="text-sm text-muted-foreground">
                    {getManagerName(hypeState.manager)} is preparing your team talk...
                  </span>
                </div>
              )}

              {/* Hype text display */}
              {hypeState.hypeText && (
                <div className="p-6">
                  <p className="text-foreground leading-relaxed italic">"{hypeState.hypeText}"</p>
                  <p className="mt-3 text-sm font-medium text-muted-foreground">
                    — {getManagerName(hypeState.manager)}
                  </p>
                </div>
              )}

              {/* Generating audio state */}
              {hypeState.status === "generating_audio" && (
                <div className="px-6 pb-6 flex items-center gap-3">
                  <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
                  <span className="text-sm text-muted-foreground">Generating audio...</span>
                </div>
              )}

              {/* Audio player */}
              {hypeState.status === "ready" && hypeState.audioUrl && (
                <div className="px-6 pb-6">
                  <AudioPlayerProvider src={hypeState.audioUrl}>
                    <div className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border">
                      <AudioPlayerButton className="h-10 w-10 text-sm" />
                      <div className="flex-1 space-y-2">
                        <AudioPlayerProgress />
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <AudioPlayerTime />
                            <span>/</span>
                            <AudioPlayerDuration />
                          </div>
                          <AudioPlayerSpeed />
                        </div>
                      </div>
                    </div>
                  </AudioPlayerProvider>

                  {/* Regenerate button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onGenerateHype(selectedManager)}
                    disabled={!canGenerate}
                    className="mt-3 text-muted-foreground hover:text-foreground disabled:opacity-50"
                    title={!canGenerate ? "Monthly limit reached" : undefined}
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    {canGenerate ? "Regenerate" : "Limit Reached"}
                  </Button>
                </div>
              )}

              {/* Error state */}
              {hypeState.status === "error" && (
                <div className="px-6 pb-6">
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-900">
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {hypeState.errorMessage || "Something went wrong. Please try again."}
                    </p>
                  </div>
                  {canGenerate && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onGenerateHype(selectedManager)}
                      className="mt-3 text-muted-foreground hover:text-foreground"
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Try again
                    </Button>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
};

type TimeUntil = {
  hours: number;
  minutes: number;
  isPast: boolean;
};

const getTimeUntil = (date: Date): TimeUntil => {
  const now = new Date();
  const diff = date.getTime() - now.getTime();

  if (diff < 0) {
    return { hours: 0, minutes: 0, isPast: true };
  }

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  return { hours, minutes, isPast: false };
};

const formatTimeUntil = ({ hours, minutes, isPast }: TimeUntil): string => {
  if (isPast) return "Now";
  if (hours > 0) return `in ${hours}h ${minutes}m`;
  if (minutes > 0) return `in ${minutes}m`;
  return "Starting now";
};
