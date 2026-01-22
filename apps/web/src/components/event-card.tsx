import { Calendar, Clock, MapPin, Users } from "lucide-react";
import { cn } from "@/lib/utils";

export type CalendarEvent = {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  location?: string;
  attendees?: number;
};

type EventCardProps = {
  event: CalendarEvent;
  onHypeMe: () => void;
  isGenerating?: boolean;
  className?: string;
};

export function EventCard({
  event,
  onHypeMe,
  isGenerating,
  className,
}: EventCardProps) {
  const timeUntil = getTimeUntil(event.start);
  const isStartingSoon = timeUntil.minutes < 30 && timeUntil.hours === 0;

  return (
    <div
      className={cn(
        "rounded-xl border bg-white p-5 shadow-sm transition-shadow hover:shadow-md",
        isStartingSoon && "border-orange-200 bg-orange-50/50",
        className
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{event.title}</h3>

          {event.description && (
            <p className="mt-1 text-sm text-gray-500 line-clamp-2">
              {event.description}
            </p>
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

        <div className="flex flex-col items-end gap-2">
          {/* Time until badge */}
          <div
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium",
              isStartingSoon
                ? "bg-orange-100 text-orange-700"
                : "bg-gray-100 text-gray-600"
            )}
          >
            {formatTimeUntil(timeUntil)}
          </div>

          {/* Hype button */}
          <button
            onClick={onHypeMe}
            disabled={isGenerating}
            className={cn(
              "rounded-lg bg-gradient-to-r from-primary-500 to-teal-500 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-primary-500/20 transition-all",
              "hover:shadow-lg hover:shadow-primary-500/30 hover:scale-105",
              "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100",
              isGenerating && "animate-pulse"
            )}
          >
            {isGenerating ? "Generating..." : "Hype Me"}
          </button>
        </div>
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

type TimeUntil = {
  hours: number;
  minutes: number;
  isPast: boolean;
};

function getTimeUntil(date: Date): TimeUntil {
  const now = new Date();
  const diff = date.getTime() - now.getTime();

  if (diff < 0) {
    return { hours: 0, minutes: 0, isPast: true };
  }

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  return { hours, minutes, isPast: false };
}

function formatTimeUntil({ hours, minutes, isPast }: TimeUntil): string {
  if (isPast) return "Now";
  if (hours > 0) return `in ${hours}h ${minutes}m`;
  if (minutes > 0) return `in ${minutes}m`;
  return "Starting now";
}
