import { Calendar, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EventCard, type CalendarEvent, type EventHypeState } from "@/components/event-card";

type EventsListProps = {
  events: CalendarEvent[] | undefined;
  isLoading: boolean;
  error: Error | null;
  getEventHypeState: (eventId: string) => EventHypeState;
  onGenerateHype: (event: CalendarEvent, managerId: string) => void;
  onRefetch: () => void;
  isRefetching: boolean;
};

export const EventsList = ({
  events,
  isLoading,
  error,
  getEventHypeState,
  onGenerateHype,
  onRefetch,
  isRefetching,
}: EventsListProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Upcoming Meetings</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefetch}
          disabled={isRefetching}
          className="text-gray-600"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {isLoading && (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <div className="animate-pulse flex flex-col items-center gap-3">
            <Calendar className="h-8 w-8 text-gray-400" />
            <p className="text-gray-500">Loading your calendar...</p>
          </div>
        </div>
      )}

      {error && (
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

      {events && events.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-8 text-center">
          <Calendar className="h-10 w-10 text-gray-400 mx-auto" />
          <p className="mt-3 text-gray-600 font-medium">No upcoming meetings</p>
          <p className="text-gray-500 text-sm mt-1">
            You're all clear for the next 24 hours!
          </p>
        </div>
      )}

      {events && events.length > 0 && (
        <div className="space-y-3">
          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              hypeState={getEventHypeState(event.id)}
              onGenerateHype={(managerId) => onGenerateHype(event, managerId)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
