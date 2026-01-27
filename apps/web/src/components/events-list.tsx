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
  isInterestRegistered?: boolean;
  isRegisteringInterest?: boolean;
  onRegisterInterest?: () => void;
};

const SkeletonCard = () => (
  <Card className="p-5">
    <div className="flex items-start justify-between gap-4">
      <div className="flex-1 space-y-3">
        <div className="h-5 w-48 bg-secondary rounded animate-pulse" />
        <div className="h-4 w-72 bg-secondary rounded animate-pulse" />
        <div className="flex gap-4 mt-3">
          <div className="h-4 w-24 bg-secondary rounded animate-pulse" />
          <div className="h-4 w-20 bg-secondary rounded animate-pulse" />
        </div>
      </div>
      <div className="flex flex-col items-end gap-3">
        <div className="h-6 w-16 bg-secondary rounded-full animate-pulse" />
        <div className="h-9 w-28 bg-secondary rounded-lg animate-pulse" />
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
  isInterestRegistered = false,
  isRegisteringInterest = false,
  onRegisterInterest,
}: EventsListProps) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-foreground">Upcoming Meetings</h2>
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
          className="text-muted-foreground"
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
        <div className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/20 p-6 text-center">
          <p className="text-red-700 dark:text-red-400 font-medium">Failed to load calendar events</p>
          <p className="text-red-600 dark:text-red-500 text-sm mt-1">{error.message}</p>
          <Button
            variant="ghost"
            onClick={onRefetch}
            className="mt-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50"
          >
            Try again
          </Button>
        </div>
      )}

      {!isLoading && events && events.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-secondary/50 p-8 text-center">
          <Calendar className="h-10 w-10 text-muted-foreground mx-auto" />
          <p className="mt-3 text-foreground font-medium">No upcoming meetings</p>
          <p className="text-muted-foreground text-sm mt-1">You're all clear for the next 24 hours!</p>
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
              isInterestRegistered={isInterestRegistered}
              isRegisteringInterest={isRegisteringInterest}
              onRegisterInterest={onRegisterInterest}
            />
          ))}
        </div>
      )}
    </div>
  );
};
