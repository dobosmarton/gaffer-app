import { Calendar, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EventCard, type CalendarEvent, type EventHypeState } from "@/components/event-card";

type EventsListProps = {
  events: CalendarEvent[] | undefined;
  isLoading: boolean;
  error: Error | null;
  getEventHypeState: (eventId: string) => EventHypeState;
  onGenerateHype: (event: CalendarEvent, managerId: string) => void;
  onRefetch: () => void;
  isRefetching: boolean;
  canGenerate?: boolean;
};

const SkeletonCard = () => (
  <Card className="p-5">
    <div className="flex items-start justify-between gap-4">
      <div className="flex-1 space-y-3">
        <div className="h-5 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-72 bg-gray-100 rounded animate-pulse" />
        <div className="flex gap-4 mt-3">
          <div className="h-4 w-24 bg-gray-100 rounded animate-pulse" />
          <div className="h-4 w-20 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
      <div className="flex flex-col items-end gap-3">
        <div className="h-6 w-16 bg-gray-100 rounded-full animate-pulse" />
        <div className="h-9 w-28 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    </div>
  </Card>
);

export const EventsList = ({
  events,
  isLoading,
  error,
  getEventHypeState,
  onGenerateHype,
  onRefetch,
  isRefetching,
  canGenerate = true,
}: EventsListProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900">Upcoming Meetings</h2>
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-amber-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading...</span>
            </div>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefetch}
          disabled={isRefetching || isLoading}
          className="text-gray-600"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {error && !isLoading && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-red-700 font-medium">Failed to load calendar events</p>
          <p className="text-red-600 text-sm mt-1">{error.message}</p>
          <Button
            variant="ghost"
            onClick={onRefetch}
            className="mt-4 bg-red-100 text-red-700 hover:bg-red-200"
          >
            Try again
          </Button>
        </div>
      )}

      {!isLoading && events && events.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center">
          <Calendar className="h-10 w-10 text-gray-400 mx-auto" />
          <p className="mt-3 text-gray-600 font-medium">No upcoming meetings</p>
          <p className="text-gray-500 text-sm mt-1">You're all clear for the next 24 hours!</p>
        </div>
      )}

      {!isLoading && events && events.length > 0 && (
        <div className="space-y-3">
          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              hypeState={getEventHypeState(event.id)}
              onGenerateHype={(managerId) => onGenerateHype(event, managerId)}
              canGenerate={canGenerate}
            />
          ))}
        </div>
      )}
    </div>
  );
};
