import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRecentAttendance } from "@/hooks/useAttendance";
import { useSSEAttendance } from "@/hooks/useSSEAttendance";
import { cn } from "@/lib/utils";
import { RefreshCw, WifiOff, ScanFace, CreditCard, Fingerprint, LogIn, LogOut } from "lucide-react";
import type { AttendanceRecord } from "@/types";

interface LiveFeedProps {
  classFilter?: string;
}

// verify_mode → Uzbek label + icon
function VerifyModeBadge({ mode }: { mode: string }) {
  const m = mode?.toLowerCase() ?? "";
  if (m === "face" || m === "facerecognition" || m.includes("face")) {
    return (
      <Badge variant="secondary" className="gap-1 text-xs">
        <ScanFace className="h-3 w-3" />
        Yuz orqali
      </Badge>
    );
  }
  if (m === "card" || m.includes("card")) {
    return (
      <Badge variant="outline" className="gap-1 text-xs">
        <CreditCard className="h-3 w-3" />
        Karta
      </Badge>
    );
  }
  if (m === "fingerprint" || m.includes("finger")) {
    return (
      <Badge variant="outline" className="gap-1 text-xs">
        <Fingerprint className="h-3 w-3" />
        Barmoq izi
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-xs">
      {mode || "—"}
    </Badge>
  );
}

// Capture image from Hikvision via proxy
function CaptureImage({ pictureUrl, studentName }: { pictureUrl: string | null; studentName: string }) {
  const [imgFailed, setImgFailed] = useState(false);

  const initials = studentName
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (pictureUrl && !imgFailed) {
    const encoded = btoa(pictureUrl);
    const src = `/api/v1/attendance/capture-image?url=${encodeURIComponent(encoded)}`;
    return (
      <img
        src={src}
        alt={studentName}
        className="h-9 w-9 rounded-full object-cover"
        onError={() => setImgFailed(true)}
      />
    );
  }

  return (
    <Avatar className="h-9 w-9">
      <AvatarFallback className="bg-primary/10 text-xs font-medium text-primary">
        {initials}
      </AvatarFallback>
    </Avatar>
  );
}

export function LiveFeed({ classFilter }: LiveFeedProps) {
  const { data, isLoading, isFetching, refetch } = useRecentAttendance(100);
  const restEvents = (data?.data?.data ?? []) as AttendanceRecord[];

  const { events: sseEvents, isConnected } = useSSEAttendance({
    classFilter,
    maxEvents: 100,
    enabled: true,
  });

  const prevRestIdsRef = useRef<Set<string>>(new Set());
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

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

  const sseEventIds = new Set(sseEvents.map((e) => `${e.student_id}-${e.event_time}`));

  const displayEvents: {
    id: string;
    student_name: string;
    class_name: string;
    device_name: string | null;
    event_type: "entry" | "exit";
    verify_mode: string;
    picture_url: string | null;
    event_time: string;
  }[] = [
    ...sseEvents.map((e) => ({
      id: `sse-${e.student_id}-${e.event_time}`,
      student_name: e.student_name,
      class_name: e.class_name,
      device_name: e.device_name ?? null,
      event_type: e.event_type,
      verify_mode: e.verify_mode ?? "face",
      picture_url: e.picture_url ?? null,
      event_time: e.event_time,
    })),
    ...restEvents
      .filter((e) => !sseEventIds.has(`${e.student_id}-${e.event_time}`))
      .map((e) => ({
        id: e.id,
        student_name: e.student_name,
        class_name: e.class_name,
        device_name: e.device_name ?? null,
        event_type: e.event_type,
        verify_mode: e.verify_mode ?? "face",
        picture_url: e.picture_url ?? null,
        event_time: e.event_time,
      })),
  ].slice(0, 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            So'nggi hodisalar
            {isConnected ? (
              <span className="flex items-center gap-1 text-xs font-normal text-green-600">
                <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
                Jonli
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
      <CardContent className="p-0">
        {isLoading && displayEvents.length === 0 ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : displayEvents.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Bugun hodisalar yo'q
          </div>
        ) : (
          <div className="max-h-[520px] overflow-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[50px]">Rasm</TableHead>
                  <TableHead>Ismi</TableHead>
                  <TableHead className="hidden sm:table-cell">Qurilma</TableHead>
                  <TableHead>Voqea</TableHead>
                  <TableHead className="hidden md:table-cell">Usul</TableHead>
                  <TableHead className="hidden md:table-cell">Status</TableHead>
                  <TableHead className="text-right">Vaqt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayEvents.map((event) => {
                  const isNew = highlightedIds.has(event.id);
                  return (
                    <TableRow
                      key={event.id}
                      className={cn(
                        "transition-colors duration-500",
                        isNew && "bg-green-50 dark:bg-green-950/30",
                      )}
                    >
                      {/* Rasm */}
                      <TableCell className="py-2">
                        <CaptureImage
                          pictureUrl={event.picture_url}
                          studentName={event.student_name}
                        />
                      </TableCell>

                      {/* Ismi */}
                      <TableCell className="py-2">
                        <p className="text-sm font-medium leading-tight">
                          {event.student_name}
                        </p>
                        {event.class_name && (
                          <p className="text-xs text-muted-foreground">
                            {event.class_name}
                          </p>
                        )}
                      </TableCell>

                      {/* Qurilma */}
                      <TableCell className="hidden py-2 text-sm text-muted-foreground sm:table-cell">
                        {event.device_name ?? "—"}
                      </TableCell>

                      {/* Voqea */}
                      <TableCell className="py-2">
                        {event.event_type === "entry" ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700 dark:bg-green-950 dark:text-green-400">
                            <LogIn className="h-3 w-3" />
                            Kirdi
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-950 dark:text-red-400">
                            <LogOut className="h-3 w-3" />
                            Chiqdi
                          </span>
                        )}
                      </TableCell>

                      {/* Usul */}
                      <TableCell className="hidden py-2 md:table-cell">
                        <VerifyModeBadge mode={event.verify_mode} />
                      </TableCell>

                      {/* Status */}
                      <TableCell className="hidden py-2 md:table-cell">
                        <Badge
                          variant="outline"
                          className="gap-1 border-green-300 text-xs text-green-700 dark:border-green-700 dark:text-green-400"
                        >
                          O'tdi
                        </Badge>
                      </TableCell>

                      {/* Vaqt */}
                      <TableCell className="py-2 text-right text-xs text-muted-foreground">
                        {new Date(
                          event.event_time.endsWith("Z") || event.event_time.includes("+")
                            ? event.event_time
                            : event.event_time + "Z",
                        ).toLocaleTimeString("uz", {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
