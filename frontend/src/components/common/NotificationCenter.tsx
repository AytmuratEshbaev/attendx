import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { useUIStore } from "@/store/uiStore";
import { useTodayAttendance } from "@/hooks/useAttendance";
import { cn } from "@/lib/utils";

export function NotificationCenter() {
  const { notifOpen, setNotifOpen, lastSeenEventId, setLastSeenEventId } =
    useUIStore();
  const { data } = useTodayAttendance();
  const events = data?.data?.data ?? [];

  const seenIdx = events.findIndex((e) => e.id === lastSeenEventId);
  const unread = seenIdx === -1 ? events.length : seenIdx;

  const handleOpen = () => {
    setNotifOpen(true);
    if (events.length > 0) {
      setLastSeenEventId(events[0].id);
    }
  };

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        onClick={handleOpen}
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </Button>

      <Sheet open={notifOpen} onOpenChange={setNotifOpen}>
        <SheetContent side="right" className="w-80 sm:w-96 flex flex-col">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              Bildirishnomalar
              {unread > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {unread} yangi
                </Badge>
              )}
            </SheetTitle>
          </SheetHeader>
          <div className="mt-4 flex-1 space-y-2 overflow-y-auto">
            {events.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Bugun hodisalar yo'q
              </p>
            ) : (
              events.map((event, i) => {
                const currentSeenIdx = events.findIndex(
                  (e) => e.id === lastSeenEventId,
                );
                const isNew =
                  currentSeenIdx === -1 ? true : i < currentSeenIdx;
                return (
                  <div
                    key={event.id}
                    className={cn(
                      "rounded-lg border p-3 text-sm",
                      isNew
                        ? "border-primary/30 bg-primary/5"
                        : "border-border bg-card",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{event.student_name}</span>
                      <Badge
                        variant={
                          event.event_type === "entry" ? "default" : "secondary"
                        }
                        className="text-xs"
                      >
                        {event.event_type === "entry" ? "Kirdi" : "Chiqdi"}
                      </Badge>
                    </div>
                    <div className="mt-1 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{event.class_name}</span>
                      <span>
                        {new Date(event.event_time).toLocaleTimeString("uz", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
