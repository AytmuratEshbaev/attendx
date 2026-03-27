import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { attendanceApi } from "@/services/attendanceApi";
import { cn } from "@/lib/utils";

const DAY_NAMES = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"];

const MONTHS_UZ = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
];

function fmt(d: Date) {
  return d.toISOString().split("T")[0];
}

function getDayColor(pct: number | null): string {
  if (pct === null) return "bg-muted text-muted-foreground";
  if (pct >= 90) return "bg-green-500 text-white";
  if (pct >= 70) return "bg-yellow-400 text-white";
  if (pct >= 50) return "bg-orange-400 text-white";
  return "bg-red-500 text-white";
}

interface AttendanceCalendarProps {
  classFilter?: string;
}

export function AttendanceCalendar({ classFilter }: AttendanceCalendarProps) {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth()); // 0-indexed

  const dateFrom = fmt(new Date(year, month, 1));
  const dateTo = fmt(new Date(year, month + 1, 0));

  const { data, isLoading } = useQuery({
    queryKey: ["attendance-calendar", year, month, classFilter],
    queryFn: () =>
      attendanceApi.list({
        per_page: 1000,
        date_from: dateFrom,
        date_to: dateTo,
        class_name: classFilter || undefined,
      }),
  });

  const { data: statsRes } = useQuery({
    queryKey: ["attendance-stats", undefined, classFilter],
    queryFn: () => attendanceApi.stats(undefined, classFilter || undefined),
  });

  const totalStudents = statsRes?.data?.data?.total_students ?? 0;
  const records = data?.data?.data ?? [];

  // Build day → present student set
  const dayMap: Record<string, Set<string>> = {};
  for (const r of records) {
    const day = r.event_time.split("T")[0];
    if (!dayMap[day]) dayMap[day] = new Set();
    dayMap[day].add(r.student_id);
  }

  // Calendar grid
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // Day of week for 1st (0=Sun, convert to Mon-first: 0=Mon..6=Sun)
  const firstDow = new Date(year, month, 1).getDay();
  const offset = firstDow === 0 ? 6 : firstDow - 1;

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  const todayStr = fmt(today);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {MONTHS_UZ[month]} {year}
          </CardTitle>
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={prevMonth}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={nextMonth}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-48 items-center justify-center text-muted-foreground text-sm">
            Yuklanmoqda...
          </div>
        ) : (
          <>
            {/* Day headers */}
            <div className="mb-1 grid grid-cols-7 gap-1 text-center text-xs font-medium text-muted-foreground">
              {DAY_NAMES.map((d) => (
                <div key={d} className="py-1">{d}</div>
              ))}
            </div>

            {/* Day cells */}
            <div className="grid grid-cols-7 gap-1">
              {/* Empty offset cells */}
              {Array.from({ length: offset }).map((_, i) => (
                <div key={`empty-${i}`} />
              ))}

              {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
                const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                const presentSet = dayMap[dateStr];
                const presentCount = presentSet?.size ?? 0;
                const pct = totalStudents > 0 && presentSet
                  ? Math.round((presentCount / totalStudents) * 100)
                  : null;
                const isToday = dateStr === todayStr;

                return (
                  <div
                    key={day}
                    className={cn(
                      "flex aspect-square items-center justify-center rounded-md text-xs font-medium transition-opacity",
                      getDayColor(pct),
                      isToday && "ring-2 ring-primary ring-offset-1",
                    )}
                    title={pct !== null ? `${presentCount}/${totalStudents} (${pct}%)` : ""}
                  >
                    {day}
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="font-medium">Rang:</span>
              {[
                { color: "bg-green-500", label: "≥90%" },
                { color: "bg-yellow-400", label: "≥70%" },
                { color: "bg-orange-400", label: "≥50%" },
                { color: "bg-red-500", label: "<50%" },
                { color: "bg-muted border", label: "Ma'lumot yo'q" },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-1">
                  <span className={cn("h-3 w-3 rounded-sm", color)} />
                  {label}
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
