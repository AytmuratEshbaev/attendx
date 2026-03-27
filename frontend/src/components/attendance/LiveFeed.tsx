import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useRecentAttendance } from "@/hooks/useAttendance";
import { useSSEAttendance } from "@/hooks/useSSEAttendance";
import { cn } from "@/lib/utils";
import { RefreshCw, WifiOff } from "lucide-react";
import type { AttendanceRecord } from "@/types";

interface LiveFeedProps {
  classFilter?: string;
}

export function LiveFeed({ classFilter }: LiveFeedProps) {
  // REST API fallback — oxirgi 100 ta hodisa (polling every 10s)
  const { data, isLoading, isFetching, refetch } = useRecentAttendance(100);
  const restEvents = (data?.data?.data ?? []) as AttendanceRecord[];

  // SSE real-time stream (preferred, falls back gracefully)
  const { events: sseEvents, isConnected } = useSSEAttendance({
    classFilter,
    maxEvents: 100,
    enabled: true,
  });

  // Merge SSE events with REST data — SSE events appear at the top
  const prevRestIdsRef = useRef<Set<string>>(new Set());
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

  // Track new REST events (when SSE is not available)
  useEffect(() => {
    if (restEvents.length === 0 || isConnected) return;

    const currentIds = new Set(restEvents.map((e) => e.id));
    const newOnes = new Set(
      [...currentIds].filter((id) => !prevRestIdsRef.current.has(id)),
    );
    prevRestIdsRef.current = currentIds;

    if (newOnes.size > 0) {
      setHighlightedIds((prev) => new Set([...prev, ...newOnes]));
      setTimeout(() => {
        setHighlightedIds((prev) => {
          const next = new Set(prev);
          newOnes.forEach((id) => next.delete(id));
          return next;
        });
      }, 3000);
    }
  }, [restEvents, isConnected]);

  // Highlight new SSE events
  useEffect(() => {
    if (sseEvents.length === 0) return;
    const latest = sseEvents[0];
    const fakeId = `${latest.student_id}-${latest.event_time}`;

    setHighlightedIds((prev) => new Set([...prev, fakeId]));
    setTimeout(() => {
      setHighlightedIds((prev) => {
        const next = new Set(prev);
        next.delete(fakeId);
        return next;
      });
    }, 3000);
  }, [sseEvents]);

  // SSE event ID larini bir xil shaklda qurish (REST bilan mos)
  const sseEventIds = new Set(sseEvents.map((e) => `${e.student_id}-${e.event_time}`));

  // Build display list: SSE events at top, then REST events (deduplicated)
  const displayEvents: { id: string; student_name: string; class_name: string; event_type: "entry" | "exit"; event_time: string }[] = [
    ...sseEvents.map((e) => ({
      id: `sse-${e.student_id}-${e.event_time}`,
      student_name: e.student_name,
      class_name: e.class_name,
      event_type: e.event_type,
      event_time: e.event_time,
    })),
    ...restEvents
      .filter((e) => !sseEventIds.has(`${e.student_id}-${e.event_time}`))
      .map((e) => ({
        id: e.id,
        student_name: e.student_name,
        class_name: e.class_name,
        event_type: e.event_type,
        event_time: e.event_time,
      })),
  ].slice(0, 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            Jonli lenta
            {isConnected ? (
              <span className="flex items-center gap-1 text-xs font-normal text-green-600">
                <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
                Jonli (SSE)
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs font-normal text-muted-foreground">
                <WifiOff className="h-3 w-3" />
                Polling
              </span>
            )}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && displayEvents.length === 0 ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : displayEvents.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Bugun hodisalar yo'q
          </div>
        ) : (
          <div className="max-h-[560px] space-y-1.5 overflow-y-auto pr-1">
            {displayEvents.map((event) => {
              const isNew = highlightedIds.has(event.id);
              return (
                <div
                  key={event.id}
                  className={cn(
                    "flex items-center justify-between rounded-lg border p-2.5 transition-colors duration-500",
                    isNew
                      ? "border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950/30"
                      : "border-border bg-card",
                  )}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{event.student_name}</p>
                    <p className="text-xs text-muted-foreground">{event.class_name}</p>
                  </div>
                  <div className="ml-2 flex-shrink-0 text-right">
                    <Badge
                      variant={event.event_type === "entry" ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {event.event_type === "entry" ? "Kirdi" : "Chiqdi"}
                    </Badge>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {new Date(
                        event.event_time.endsWith("Z") || event.event_time.includes("+")
                          ? event.event_time
                          : event.event_time + "Z"
                      ).toLocaleTimeString("uz", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
