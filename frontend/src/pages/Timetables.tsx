import { useState } from "react";
import {
  Plus,
  Trash2,
  CalendarDays,
  Clock,
  ChevronRight,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import {
  useTimetables,
  useCreateTimetable,
  useDeleteTimetable,
} from "@/hooks/useTimetables";
import type { Timetable, TimetableCreate } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ALL_WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

const DAY_LABELS: Record<string, string> = {
  Monday: "Du",
  Tuesday: "Se",
  Wednesday: "Ch",
  Thursday: "Pa",
  Friday: "Ju",
  Saturday: "Sh",
  Sunday: "Ya",
};

function fmtTime(t: string | null) {
  if (!t) return "—";
  return t.slice(0, 5);
}

function fmtDate(d: string | null) {
  if (!d) return "—";
  return d;
}

function toApiTime(t: string) {
  return t.length === 5 ? `${t}:00` : t;
}

// ---------------------------------------------------------------------------
// Timetable card
// ---------------------------------------------------------------------------

function TimetableCard({
  timetable,
  onDelete,
}: {
  timetable: Timetable;
  onDelete: () => void;
}) {
  const isRecurring = timetable.timetable_type === "recurring";

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div className="space-y-1">
          <CardTitle className="text-base flex items-center gap-2">
            {timetable.name}
            {!timetable.is_active && (
              <Badge variant="secondary" className="text-xs">
                Faol emas
              </Badge>
            )}
          </CardTitle>
          <Badge
            variant={isRecurring ? "default" : "outline"}
            className="text-xs"
          >
            {isRecurring ? "Takroriy" : "Bir martalik"}
          </Badge>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground mt-1 flex-shrink-0" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1 text-sm text-muted-foreground">
          {isRecurring ? (
            <>
              <div className="flex items-center gap-2">
                <CalendarDays className="h-3.5 w-3.5" />
                <span>
                  {(timetable.weekdays ?? [])
                    .map((d) => DAY_LABELS[d] ?? d)
                    .join(", ") || "—"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5" />
                <span>
                  {fmtTime(timetable.start_time)} – {fmtTime(timetable.end_time)}
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <CalendarDays className="h-3.5 w-3.5" />
                <span>
                  {fmtDate(timetable.date_from)} – {fmtDate(timetable.date_to)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5" />
                <span>
                  {fmtTime(timetable.ot_start_time)} – {fmtTime(timetable.ot_end_time)}
                </span>
              </div>
            </>
          )}
        </div>
        {timetable.description && (
          <p className="text-xs text-muted-foreground">{timetable.description}</p>
        )}
        <div
          className="flex justify-end border-t pt-2"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Create dialog
// ---------------------------------------------------------------------------

type RecurringForm = {
  timetable_type: "recurring";
  name: string;
  description: string;
  weekdays: string[];
  start_time: string;
  end_time: string;
  is_active: boolean;
};

type OneTimeForm = {
  timetable_type: "one_time";
  name: string;
  description: string;
  date_from: string;
  date_to: string;
  ot_start_time: string;
  ot_end_time: string;
  is_active: boolean;
};

const EMPTY_RECURRING: RecurringForm = {
  timetable_type: "recurring",
  name: "",
  description: "",
  weekdays: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  start_time: "08:00",
  end_time: "17:00",
  is_active: true,
};

const EMPTY_ONE_TIME: OneTimeForm = {
  timetable_type: "one_time",
  name: "",
  description: "",
  date_from: "",
  date_to: "",
  ot_start_time: "09:00",
  ot_end_time: "17:00",
  is_active: true,
};

function CreateTimetableDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [type, setType] = useState<"recurring" | "one_time">("recurring");
  const [recurring, setRecurring] = useState<RecurringForm>({ ...EMPTY_RECURRING });
  const [oneTime, setOneTime] = useState<OneTimeForm>({ ...EMPTY_ONE_TIME });

  const createTimetable = useCreateTimetable();

  const handleClose = () => {
    setRecurring({ ...EMPTY_RECURRING });
    setOneTime({ ...EMPTY_ONE_TIME });
    setType("recurring");
    onClose();
  };

  const toggleDay = (day: string) => {
    setRecurring((prev) => ({
      ...prev,
      weekdays: prev.weekdays.includes(day)
        ? prev.weekdays.filter((d) => d !== day)
        : [...prev.weekdays, day],
    }));
  };

  const handleSubmit = () => {
    let payload: TimetableCreate;
    if (type === "recurring") {
      payload = {
        timetable_type: "recurring",
        name: recurring.name,
        description: recurring.description || undefined,
        weekdays: recurring.weekdays,
        start_time: toApiTime(recurring.start_time),
        end_time: toApiTime(recurring.end_time),
        is_active: recurring.is_active,
      };
    } else {
      payload = {
        timetable_type: "one_time",
        name: oneTime.name,
        description: oneTime.description || undefined,
        date_from: oneTime.date_from,
        date_to: oneTime.date_to,
        ot_start_time: toApiTime(oneTime.ot_start_time),
        ot_end_time: toApiTime(oneTime.ot_end_time),
        is_active: oneTime.is_active,
      };
    }
    createTimetable.mutate(payload, { onSuccess: handleClose });
  };

  const isValid =
    type === "recurring"
      ? !!recurring.name &&
        recurring.weekdays.length > 0 &&
        !!recurring.start_time &&
        !!recurring.end_time
      : !!oneTime.name &&
        !!oneTime.date_from &&
        !!oneTime.date_to &&
        !!oneTime.ot_start_time &&
        !!oneTime.ot_end_time;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Yangi dars jadvali</DialogTitle>
          <DialogDescription>
            Takroriy yoki bir martalik dars jadvali yarating
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Type selector */}
          <div className="flex rounded-md border">
            {(["recurring", "one_time"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={cn(
                  "flex-1 py-2 text-sm font-medium transition-colors first:rounded-l-sm last:rounded-r-sm",
                  type === t
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {t === "recurring" ? "Takroriy" : "Bir martalik"}
              </button>
            ))}
          </div>

          <div className="space-y-2">
            <Label>Nomi *</Label>
            <Input
              value={type === "recurring" ? recurring.name : oneTime.name}
              onChange={(e) =>
                type === "recurring"
                  ? setRecurring((p) => ({ ...p, name: e.target.value }))
                  : setOneTime((p) => ({ ...p, name: e.target.value }))
              }
              placeholder="Du-Ju 08:00-17:00"
            />
          </div>

          <div className="space-y-2">
            <Label>Tavsif</Label>
            <Input
              value={
                type === "recurring" ? recurring.description : oneTime.description
              }
              onChange={(e) =>
                type === "recurring"
                  ? setRecurring((p) => ({ ...p, description: e.target.value }))
                  : setOneTime((p) => ({ ...p, description: e.target.value }))
              }
              placeholder="Ixtiyoriy"
            />
          </div>

          {type === "recurring" && (
            <>
              <div className="space-y-2">
                <Label>Kunlar *</Label>
                <div className="flex flex-wrap gap-2">
                  {ALL_WEEKDAYS.map((day) => (
                    <button
                      key={day}
                      onClick={() => toggleDay(day)}
                      className={cn(
                        "h-8 w-8 rounded-full text-xs font-medium border transition-colors",
                        recurring.weekdays.includes(day)
                          ? "bg-primary text-primary-foreground border-primary"
                          : "border-input text-muted-foreground hover:bg-muted",
                      )}
                    >
                      {DAY_LABELS[day]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Boshlanish vaqti *</Label>
                  <Input
                    type="time"
                    value={recurring.start_time}
                    onChange={(e) =>
                      setRecurring((p) => ({ ...p, start_time: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tugash vaqti *</Label>
                  <Input
                    type="time"
                    value={recurring.end_time}
                    onChange={(e) =>
                      setRecurring((p) => ({ ...p, end_time: e.target.value }))
                    }
                  />
                </div>
              </div>
            </>
          )}

          {type === "one_time" && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Boshlanish sanasi *</Label>
                  <Input
                    type="date"
                    value={oneTime.date_from}
                    onChange={(e) =>
                      setOneTime((p) => ({ ...p, date_from: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tugash sanasi *</Label>
                  <Input
                    type="date"
                    value={oneTime.date_to}
                    onChange={(e) =>
                      setOneTime((p) => ({ ...p, date_to: e.target.value }))
                    }
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Boshlanish vaqti *</Label>
                  <Input
                    type="time"
                    value={oneTime.ot_start_time}
                    onChange={(e) =>
                      setOneTime((p) => ({ ...p, ot_start_time: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tugash vaqti *</Label>
                  <Input
                    type="time"
                    value={oneTime.ot_end_time}
                    onChange={(e) =>
                      setOneTime((p) => ({ ...p, ot_end_time: e.target.value }))
                    }
                  />
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Bekor qilish
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={createTimetable.isPending || !isValid}
          >
            {createTimetable.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Yaratish
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function Timetables() {
  const [filterType, setFilterType] = useState<"" | "recurring" | "one_time">(
    "",
  );
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data, isLoading } = useTimetables(filterType || undefined);
  const deleteTimetable = useDeleteTimetable();

  const timetables: Timetable[] = data?.data?.data ?? [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Dars jadvallari"
        description={`${timetables.length} ta jadval`}
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Yangi jadval
          </Button>
        }
      />

      <div className="flex rounded-md border w-fit">
        {(
          [
            { value: "", label: "Barchasi" },
            { value: "recurring", label: "Takroriy" },
            { value: "one_time", label: "Bir martalik" },
          ] as const
        ).map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilterType(opt.value)}
            className={cn(
              "px-4 py-1.5 text-sm font-medium transition-colors first:rounded-l-sm last:rounded-r-sm",
              filterType === opt.value
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted",
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-28 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : timetables.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Dars jadvallari topilmadi"
          description="Yangi takroriy yoki bir martalik jadval yarating"
          action={
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Yangi jadval
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {timetables.map((tt) => (
            <TimetableCard
              key={tt.id}
              timetable={tt}
              onDelete={() => setDeleteId(tt.id)}
            />
          ))}
        </div>
      )}

      <CreateTimetableDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />

      <ConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="Dars jadvalini o'chirish"
        description="Bu amalni bekor qilib bo'lmaydi. Dars jadvali butunlay o'chiriladi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteId !== null) {
            deleteTimetable.mutate(deleteId, {
              onSuccess: () => setDeleteId(null),
            });
          }
        }}
      />
    </div>
  );
}
