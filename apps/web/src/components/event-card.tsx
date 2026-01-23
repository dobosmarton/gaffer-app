import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Clock, MapPin, Users, ChevronDown, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AudioPlayerProvider,
  AudioPlayerButton,
  AudioPlayerProgress,
  AudioPlayerTime,
  AudioPlayerDuration,
  AudioPlayerSpeed,
} from "@/components/ui/audio-player";
import { cn } from "@/lib/utils";
import { MANAGERS, getManagerName } from "@/components/manager-selector";

export type CalendarEvent = {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  location?: string;
  attendees?: number;
};

export type EventHypeState = {
  status: "idle" | "generating_text" | "generating_audio" | "ready" | "error";
  hypeText: string | null;
  audioUrl: string | null;
  manager: string;
};

type EventCardProps = {
  event: CalendarEvent;
  hypeState: EventHypeState;
  onGenerateHype: (managerId: string) => void;
  className?: string;
};

export const EventCard = ({ event, hypeState, onGenerateHype, className }: EventCardProps) => {
  const [selectedManager, setSelectedManager] = useState("ferguson");
  const timeUntil = getTimeUntil(event.start);
  const isStartingSoon = timeUntil.minutes < 30 && timeUntil.hours === 0;
  const isGenerating =
    hypeState.status === "generating_text" || hypeState.status === "generating_audio";
  const hasContent = hypeState.status !== "idle";
  const selectedManagerData = MANAGERS.find((m) => m.id === selectedManager);

  return (
    <Card
      className={cn(
        "overflow-hidden transition-shadow hover:shadow-md",
        isStartingSoon && "border-orange-200 bg-orange-50/50",
        className
      )}
    >
      {/* Main event info */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{event.title}</h3>

            {event.description && (
              <p className="mt-1 text-sm text-gray-500 line-clamp-2">{event.description}</p>
            )}

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-gray-400" />
                <span>
                  {formatTime(event.start)} - {formatTime(event.end)}
                </span>
              </div>

              {event.location && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <span className="truncate max-w-[150px]">{event.location}</span>
                </div>
              )}

              {event.attendees && event.attendees > 1 && (
                <div className="flex items-center gap-1.5">
                  <Users className="h-4 w-4 text-gray-400" />
                  <span>{event.attendees} attendees</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <Badge
              variant={isStartingSoon ? "destructive" : "secondary"}
              className={cn(
                "rounded-full",
                isStartingSoon
                  ? "bg-orange-100 text-orange-700 border-orange-200"
                  : "bg-gray-100 text-gray-600"
              )}
            >
              {formatTimeUntil(timeUntil)}
            </Badge>

            {/* Manager selector + Hype button */}
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={isGenerating}
                    className="h-9 gap-1.5"
                  >
                    <span className="text-base">{selectedManagerData?.emoji}</span>
                    <span className="hidden sm:inline text-xs max-w-[80px] truncate">
                      {selectedManagerData?.name.split(" ").pop()}
                    </span>
                    <ChevronDown className="h-3 w-3 opacity-50" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  {MANAGERS.map((manager) => (
                    <DropdownMenuItem
                      key={manager.id}
                      onClick={() => setSelectedManager(manager.id)}
                      className={cn(
                        "flex items-center gap-2",
                        selectedManager === manager.id && "bg-gray-100"
                      )}
                    >
                      <span className="text-lg">{manager.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm">{manager.name}</p>
                        <p className="text-xs text-gray-500 truncate">{manager.description}</p>
                      </div>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                onClick={() => onGenerateHype(selectedManager)}
                disabled={isGenerating}
                size="sm"
                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-md"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="hidden sm:inline ml-1">Generating...</span>
                  </>
                ) : (
                  "Hype Me"
                )}
              </Button>
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
            <div className="border-t border-gray-100 bg-gray-50/50">
              {/* Generating text state */}
              {hypeState.status === "generating_text" && (
                <div className="p-6 flex items-center justify-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-amber-500" />
                  <span className="text-sm text-gray-600">
                    {getManagerName(hypeState.manager)} is preparing your team talk...
                  </span>
                </div>
              )}

              {/* Hype text display */}
              {hypeState.hypeText && (
                <div className="p-6">
                  <p className="text-gray-700 leading-relaxed italic">"{hypeState.hypeText}"</p>
                  <p className="mt-3 text-sm font-medium text-gray-500">
                    — {getManagerName(hypeState.manager)}
                  </p>
                </div>
              )}

              {/* Generating audio state */}
              {hypeState.status === "generating_audio" && (
                <div className="px-6 pb-6 flex items-center gap-3">
                  <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
                  <span className="text-sm text-gray-500">Generating audio...</span>
                </div>
              )}

              {/* Audio player */}
              {hypeState.status === "ready" && hypeState.audioUrl && (
                <div className="px-6 pb-6">
                  <AudioPlayerProvider src={hypeState.audioUrl}>
                    <div className="flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200">
                      <AudioPlayerButton className="h-10 w-10 text-sm" />
                      <div className="flex-1 space-y-2">
                        <AudioPlayerProgress />
                        <div className="flex items-center justify-between text-xs text-gray-500">
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
                    className="mt-3 text-gray-500 hover:text-gray-700"
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Regenerate
                  </Button>
                </div>
              )}

              {/* Error state */}
              {hypeState.status === "error" && (
                <div className="px-6 pb-6">
                  <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                    <p className="text-sm text-red-600">Something went wrong. Please try again.</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onGenerateHype(selectedManager)}
                    className="mt-3 text-gray-500 hover:text-gray-700"
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Try again
                  </Button>
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
