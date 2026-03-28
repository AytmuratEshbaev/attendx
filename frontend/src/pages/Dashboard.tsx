import { useEffect, useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { attendanceApi } from "@/services/attendanceApi";
import type { DeviceLiveEvent } from "@/types";
import { useSSEAttendance } from "@/hooks/useSSEAttendance";
import { useAuthStore } from "@/store/authStore";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import {
  RefreshCw,
  UserCheck,
  LogIn,
  LogOut,
  Fingerprint,
  CreditCard,
  ScanFace,
  ImageOff,
  UserCircle,
} from "lucide-react";

// ─── Face Photo Modal ──────────────────────────────────────────────────────
interface FaceModalProps {
  studentId: string | null;
  studentName: string;
  captureUrl?: string | null;
  open: boolean;
  onClose: () => void;
}

function FaceModal({ studentId, studentName, captureUrl, open, onClose }: FaceModalProps) {
  const [src, setSrc] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(false);
    setSrc("");

    // Birinchi: qurilma capture rasmi (yangi hodisalar uchun)
    if (captureUrl) {
      const encoded = encodeURIComponent(btoa(captureUrl));
      fetch(`/api/v1/attendance/capture-image?url=${encoded}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("not found");
          return res.blob();
        })
        .then((blob) => { setSrc(URL.createObjectURL(blob)); setLoading(false); })
        .catch(() => {
          // Capture rasm yuklanmasa, profil rasmiga o'tish
          if (studentId) fetchFacePhoto(studentId); // fetchFacePhoto handles setLoading(false)
          else { setError(true); setLoading(false); }
        });
      return;
    }

    // Ikkinchi: saqlangan profil rasmi
    if (studentId) fetchFacePhoto(studentId);
    else { setError(true); setLoading(false); }

    function fetchFacePhoto(id: string) {
      fetch(`/api/v1/students/${id}/face`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("not found");
          return res.blob();
        })
        .then((blob) => setSrc(URL.createObjectURL(blob)))
        .catch(() => setError(true))
        .finally(() => setLoading(false));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, studentId, captureUrl]);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>{studentName}</DialogTitle>
        </DialogHeader>
        <div className="flex items-center justify-center min-h-[280px] bg-muted rounded-md overflow-hidden">
          {loading ? (
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          ) : error ? (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <ImageOff className="h-12 w-12 opacity-30" />
              <span className="text-sm">Rasm topilmadi</span>
            </div>
          ) : src ? (
            <img src={src} alt={studentName} className="w-full h-full object-contain max-h-[400px]" />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Real-Time Events ──────────────────────────────────────────────────────
const VERIFY_LABELS: Record<string, { label: string; icon: React.ElementType }> = {
  face: { label: "Yuz orqali", icon: ScanFace },
  fingerprint: { label: "Barmoq izi", icon: Fingerprint },
  card: { label: "Karta", icon: CreditCard },
};

// Inline photo loader — tries capture URL, falls back to profile face
function EventPhoto({ studentId, captureUrl }: { studentId: string | null; captureUrl?: string | null }) {
  const [src, setSrc] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    setLoading(true);
    setError(false);
    setSrc("");

    function fetchFace(id: string) {
      fetch(`/api/v1/students/${id}/face`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
        .then((r) => { if (!r.ok) throw new Error(); return r.blob(); })
        .then((b) => setSrc(URL.createObjectURL(b)))
        .catch(() => setError(true))
        .finally(() => setLoading(false));
    }

    if (captureUrl) {
      const encoded = encodeURIComponent(btoa(captureUrl));
      fetch(`/api/v1/attendance/capture-image?url=${encoded}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
        .then((r) => { if (!r.ok) throw new Error(); return r.blob(); })
        .then((b) => { setSrc(URL.createObjectURL(b)); setLoading(false); })
        .catch(() => {
          if (studentId) {
            fetchFace(studentId); // fetchFace handles setLoading(false) itself
          } else {
            setError(true);
            setLoading(false);
          }
        });
    } else if (studentId) {
      fetchFace(studentId);
    } else {
      setError(true);
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentId, captureUrl]);

  if (loading) return (
    <div className="flex h-full w-full items-center justify-center bg-muted">
      <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
  if (error || !src) return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-muted text-muted-foreground">
      <ImageOff className="h-10 w-10 opacity-30" />
      <span className="text-xs">Rasm yo'q</span>
    </div>
  );
  return <img src={src} alt="" className="h-full w-full object-cover" />;
}

interface EventItem {
  student_id?: string;
  student_name?: string;
  class_name?: string;
  category_name?: string | null;
  device_name?: string;
  event_type?: string;
  event_time?: string;
  verify_mode?: string;
  picture_url?: string | null;
}

// Last event hero card — photo left, details right
function LastEventCard({ ev }: { ev: EventItem }) {
  const isEntry = ev.event_type === "entry";
  const verify = VERIFY_LABELS[ev.verify_mode ?? "face"] ?? VERIFY_LABELS.face;
  const VerifyIcon = verify.icon;

  return (
    <div
      className={cn(
        "flex rounded-xl overflow-hidden border transition-all duration-300 premium-shadow glass-panel group hover:shadow-2xl hover:-translate-y-1 relative z-10",
        isEntry ? "border-success/30 bg-success/5 dark:bg-success/10" : "border-red-500/30 bg-red-500/5 dark:bg-red-500/10"
      )}
    >
      <div className={cn(
        "absolute inset-0 bg-gradient-to-r opacity-10 blur-xl -z-10 transition-opacity group-hover:opacity-20",
        isEntry ? "from-success" : "from-red-500"
      )} />
      {/* Photo */}
      <div className="relative w-64 shrink-0 h-64">
        <EventPhoto studentId={ev.student_id ?? null} captureUrl={ev.picture_url} />
        {/* Entry/exit badge overlay */}
        <div className={cn(
          "absolute bottom-3 left-3 flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-bold text-white shadow-lg backdrop-blur-md",
          isEntry ? "bg-success/90 dark:bg-success/80" : "bg-red-600/90 dark:bg-red-600/80"
        )}>
          {isEntry ? <LogIn className="h-4 w-4" /> : <LogOut className="h-4 w-4" />}
          {isEntry ? "Kirdi" : "Chiqdi"}
        </div>
      </div>

      {/* Details */}
      <div className="flex flex-col justify-center gap-4 px-6 py-5 flex-1 min-w-0">
        <div>
          <p className="text-2xl font-bold truncate">{ev.student_name ?? "—"}</p>
          {ev.class_name && (
            <p className="text-base text-muted-foreground mt-1">{ev.class_name}</p>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          <span className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-wider",
            isEntry ? "bg-success/20 text-success dark:bg-success/20 dark:text-success"
                    : "bg-orange-500/20 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400"
          )}>
            <VerifyIcon className="h-4 w-4" />
            {verify.label}
          </span>
          {ev.device_name && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1.5 text-sm text-muted-foreground">
              {ev.device_name}
            </span>
          )}
        </div>

        <p className={cn(
          "text-4xl font-mono font-black tabular-nums tracking-tight mt-auto",
          isEntry ? "text-success dark:text-success text-glow" : "text-red-600 dark:text-red-500 text-shadow"
        )}>
          {ev.event_time
            ? new Date(ev.event_time).toLocaleTimeString("uz", {
                hour: "2-digit", minute: "2-digit", second: "2-digit",
                timeZone: "Asia/Tashkent",
              })
            : "—"}
        </p>
        <p className="text-sm text-muted-foreground font-mono">
          {ev.event_time
            ? new Date(ev.event_time).toLocaleDateString("uz", {
                day: "2-digit", month: "2-digit", year: "numeric",
                timeZone: "Asia/Tashkent",
              })
            : ""}
        </p>
      </div>
    </div>
  );
}

// Unified display type for events from all sources (extends EventItem for LastEventCard compat)
interface DisplayEvent extends EventItem {
  key: string;
  student_name: string;
  category_name?: string | null;
  device_name: string;
  event_type: "entry" | "exit";
  event_time: string;
  verify_mode: string;
}

function RealTimeEvents() {
  const { events: sseEvents, isConnected } = useSSEAttendance({ enabled: true, maxEvents: 100 });
  const [modal, setModal] = useState<{ studentId: string; studentName: string; captureUrl?: string | null } | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [deviceEvents, setDeviceEvents] = useState<DeviceLiveEvent[]>([]);

  const { data: historyData, isFetching: isHistoryFetching } = useQuery({
    queryKey: ["attendance", "recent"],
    queryFn: () => attendanceApi.recent(100),
    refetchInterval: 30_000,
    staleTime: 0,
  });

  async function handleDeviceRefresh() {
    setIsRefreshing(true);
    try {
      const res = await attendanceApi.deviceLive(24, 100);
      setDeviceEvents(res.data?.data ?? []);
    } finally {
      setIsRefreshing(false);
    }
  }

  const events = useMemo((): DisplayEvent[] => {
    const seen = new Set<string>();

    const fromSSE: DisplayEvent[] = sseEvents.map((e) => ({
      key: `${e.student_id}_${e.event_time}`,
      student_id: e.student_id,
      student_name: e.student_name,
      class_name: e.class_name,
      category_name: (e as { category_name?: string | null }).category_name ?? null,
      device_name: e.device_name,
      event_type: e.event_type as "entry" | "exit",
      event_time: e.event_time,
      verify_mode: e.verify_mode,
      picture_url: e.picture_url,
    }));

    const fromHistory: DisplayEvent[] = ((historyData?.data?.data ?? []) as typeof sseEvents).map((e) => ({
      key: `${e.student_id}_${e.event_time}`,
      student_id: e.student_id,
      student_name: e.student_name,
      class_name: e.class_name,
      category_name: (e as { category_name?: string | null }).category_name ?? null,
      device_name: e.device_name,
      event_type: e.event_type as "entry" | "exit",
      event_time: e.event_time,
      verify_mode: e.verify_mode,
      picture_url: (e as { picture_url?: string | null }).picture_url,
    }));

    const fromDevice: DisplayEvent[] = deviceEvents.map((e) => ({
      key: `${e.employee_no}_${e.event_time}`,
      student_name: e.student_name,
      device_name: e.device_name,
      event_type: e.event_type,
      event_time: e.event_time,
      verify_mode: e.verify_mode,
      picture_url: e.picture_url,
    }));

    return [...fromSSE, ...fromDevice, ...fromHistory]
      .filter((e) => {
        if (seen.has(e.key)) return false;
        seen.add(e.key);
        return true;
      })
      .sort((a, b) => new Date(b.event_time).getTime() - new Date(a.event_time).getTime())
      .slice(0, 100);
  }, [sseEvents, historyData, deviceEvents]);

  const latest = events[0] ?? null;
  const rest = events.slice(1);

  return (
    <div className="flex flex-col h-full min-h-0 py-2">
      <Card className="flex flex-col h-full min-h-0 glass-card border-none">
        <CardHeader className="flex-row items-center justify-between pb-4 shrink-0 border-b border-border/50 bg-white/30 dark:bg-slate-900/30 rounded-t-xl backdrop-blur-md mb-4">
          <CardTitle className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">So'nggi hodisalar</CardTitle>
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                "gap-1 text-xs",
                isConnected ? "border-green-300 text-green-600" : "border-orange-300 text-orange-500"
              )}
            >
              <span className={cn("h-1.5 w-1.5 rounded-full", isConnected ? "bg-green-500 animate-pulse" : "bg-orange-400")} />
              {isConnected ? "Jonli" : "Polling"}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleDeviceRefresh}
              disabled={isRefreshing || isHistoryFetching}
              title="Qurilmalardan so'ngi 24 soatlik eventlarni olish"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", (isRefreshing || isHistoryFetching) && "animate-spin")} />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex flex-col gap-3 pt-0 flex-1 min-h-0 overflow-hidden">
          {/* Latest event hero */}
          {latest ? (
            <LastEventCard key={latest.key} ev={latest} />
          ) : (
            <div className="flex items-center justify-center rounded-lg border border-dashed py-10 text-muted-foreground">
              Hodisalar yo'q
            </div>
          )}

          {/* Rest of events table */}
          {rest.length > 0 && (
            <div className="flex-1 min-h-0 overflow-auto rounded-xl border border-border/50 bg-white/40 dark:bg-slate-950/40 backdrop-blur-md shadow-inner">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-border/50 z-10">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Ismi</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Guruh</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Qurilma</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Voqea</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Nima orqali</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Vaqt</th>
                    <th className="px-4 py-2 text-center font-medium text-muted-foreground">Rasm</th>
                  </tr>
                </thead>
                <tbody>
                  {rest.map((ev, i) => {
                    const verify = VERIFY_LABELS[ev.verify_mode ?? "face"] ?? VERIFY_LABELS.face;
                    const VerifyIcon = verify.icon;
                    const isEntry = ev.event_type === "entry";
                    return (
                      <tr
                        key={`${ev.key}-${i}`}
                        className="border-b last:border-0 hover:bg-muted/50 transition-colors"
                      >
                        {/* Ismi */}
                        <td className="px-4 py-2 font-medium">{ev.student_name ?? "—"}</td>

                        {/* Guruh */}
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {ev.category_name ?? ev.class_name ?? "—"}
                        </td>

                        {/* Qurilma */}
                        <td className="px-4 py-2 text-xs text-muted-foreground">{ev.device_name ?? "—"}</td>

                        {/* Voqea */}
                        <td className="px-4 py-2">
                          {isEntry ? (
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
                        </td>

                        {/* Nima orqali */}
                        <td className="px-4 py-2">
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            <VerifyIcon className="h-3 w-3" />
                            {verify.label}
                          </span>
                        </td>

                        {/* Vaqt */}
                        <td className="px-4 py-2 text-xs text-muted-foreground">
                          {ev.event_time ? (
                            <>
                              <span>
                                {new Date(ev.event_time).toLocaleDateString("uz", {
                                  day: "2-digit", month: "2-digit", year: "numeric",
                                  timeZone: "Asia/Tashkent",
                                })}
                              </span>
                              <br />
                              <span>
                                {new Date(ev.event_time).toLocaleTimeString("uz", {
                                  hour: "2-digit", minute: "2-digit", second: "2-digit",
                                  timeZone: "Asia/Tashkent",
                                })}
                              </span>
                            </>
                          ) : "—"}
                        </td>

                        {/* Rasm */}
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={() =>
                              ev.student_id
                                ? setModal({ studentId: ev.student_id, studentName: ev.student_name ?? "—", captureUrl: ev.picture_url })
                                : ev.picture_url && setModal({ studentId: "", studentName: ev.student_name ?? "—", captureUrl: ev.picture_url })
                            }
                            className="inline-flex items-center justify-center rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                            title="Rasmni ko'rish"
                          >
                            <UserCircle className="h-5 w-5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <FaceModal
        open={!!modal}
        studentId={modal?.studentId ?? null}
        studentName={modal?.studentName ?? ""}
        captureUrl={modal?.captureUrl}
        onClose={() => setModal(null)}
      />
    </div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────
export default function Dashboard() {
  return (
    <div className="flex flex-col h-full min-h-0">
      <RealTimeEvents />
    </div>
  );
}
