import { useState, useMemo } from "react";
import { toast } from "sonner";
import {
  Download,
  Loader2,
  RefreshCw,
  Users,
  UserCheck,
  UserX,
  TrendingUp,
  List,
  CalendarDays,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

import { attendanceApi } from "@/services/attendanceApi";
import { getErrorMessage } from "@/services/api";
import { useAttendanceList, useAttendanceStats } from "@/hooks/useAttendance";
import { useDevices } from "@/hooks/useDevices";
import { useDownload } from "@/hooks/useDownload";
import { PageHeader } from "@/components/common/PageHeader";
import { FilterPanel } from "@/components/common/FilterPanel";
import { AttendanceCalendar } from "@/components/attendance/AttendanceCalendar";
import { StudentSidePanel } from "@/components/students/StudentSidePanel";
import { LiveFeed } from "@/components/attendance/LiveFeed";
import { GroupStats } from "@/components/attendance/GroupStats";
import { useUIStore } from "@/store/uiStore";
import type { AttendanceFilters } from "@/types";

const EMPTY_FILTERS: AttendanceFilters = {
  class_name: "",
  date_from: "",
  date_to: "",
  event_type: "",
  device_name: "",
};

export default function Attendance() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AttendanceFilters>(EMPTY_FILTERS);
  const [exporting, setExporting] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const { download } = useDownload();
  const { attendanceView, setAttendanceView } = useUIStore();

  const isToday = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];
    return filters.date_from === today && filters.date_to === today;
  }, [filters.date_from, filters.date_to]);

  const { data, isLoading } = useAttendanceList({
    page,
    per_page: 25,
    class_name: filters.class_name || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    event_type: filters.event_type || undefined,
  });

  const { data: statsRes, isLoading: statsLoading } = useAttendanceStats(
    undefined,
    filters.class_name || undefined,
  );

  const { data: devicesRes } = useDevices();
  const devices = (devicesRes?.data?.data ?? []).map((d) => d.name);

  const stats = statsRes?.data?.data;
  let records = data?.data?.data ?? [];
  const pagination = data?.data?.pagination;

  // Client-side device filter (API doesn't support it)
  if (filters.device_name) {
    records = records.filter((r) => r.device_name === filters.device_name);
  }

  const classes = Object.keys(stats?.by_class ?? {});

  const handleFiltersChange = (newFilters: AttendanceFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const handleExport = async () => {
    if (!filters.date_from || !filters.date_to) {
      toast.error("Iltimos, sana oralig'ini tanlang");
      return;
    }
    setExporting(true);
    try {
      const res = await attendanceApi.report({
        date_from: filters.date_from,
        date_to: filters.date_to,
        class_name: filters.class_name || undefined,
        format: "xlsx",
      });
      download(
        new Blob([res.data]),
        `attendance-${filters.date_from}-${filters.date_to}.xlsx`,
      );
      toast.success("Hisobot yuklandi");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Davomat"
        description="Barcha davomat yozuvlari"
        actions={
          <div className="flex items-center gap-2">
            {/* View toggle */}
            <div className="flex rounded-md border">
              <Button
                variant={attendanceView === "table" ? "secondary" : "ghost"}
                size="sm"
                className="rounded-r-none border-0"
                onClick={() => setAttendanceView("table")}
              >
                <List className="h-4 w-4" />
              </Button>
              <Button
                variant={attendanceView === "calendar" ? "secondary" : "ghost"}
                size="sm"
                className="rounded-l-none border-0"
                onClick={() => setAttendanceView("calendar")}
              >
                <CalendarDays className="h-4 w-4" />
              </Button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={exporting || !filters.date_from || !filters.date_to}
            >
              {exporting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              Eksport
            </Button>
          </div>
        }
      />

      {/* Stats bar */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {([
          {
            title: "Jami",
            value: stats?.total_students ?? 0,
            icon: Users,
            color: "text-blue-600",
          },
          {
            title: "Keldi",
            value: stats?.present_today ?? 0,
            icon: UserCheck,
            color: "text-green-600",
          },
          {
            title: "Kelmadi",
            value: stats?.absent_today ?? 0,
            icon: UserX,
            color: "text-red-600",
          },
          {
            title: "Foiz",
            value: `${stats?.attendance_percentage ?? 0}%`,
            icon: TrendingUp,
            color: "text-orange-600",
          },
        ] as const).map((item) => (
          <Card key={item.title}>
            <CardContent className="flex items-center gap-3 pb-4 pt-4">
              <div className="rounded-md bg-muted p-2">
                <item.icon className={`h-4 w-4 ${item.color}`} />
              </div>
              {statsLoading ? (
                <Skeleton className="h-6 w-16" />
              ) : (
                <div>
                  <p className="text-lg font-bold">{item.value}</p>
                  <p className="text-xs text-muted-foreground">{item.title}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <FilterPanel
        filters={filters}
        onChange={handleFiltersChange}
        classes={classes}
        devices={devices}
      />

      {isToday && (
        <Badge variant="outline" className="gap-1 text-green-600 w-fit">
          <RefreshCw className="h-3 w-3 animate-spin" />
          Avtomatik yangilanmoqda
        </Badge>
      )}

      {/* Calendar or Table view */}
      {attendanceView === "calendar" ? (
        <AttendanceCalendar classFilter={filters.class_name} />
      ) : (
        <>
          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>O'quvchi</TableHead>
                  <TableHead>Sinf</TableHead>
                  <TableHead>Vaqt</TableHead>
                  <TableHead>Turi</TableHead>
                  <TableHead>Qurilma</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i}>
                        {Array.from({ length: 5 }).map((_, j) => (
                          <TableCell key={j}>
                            <Skeleton className="h-5 w-full" />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  : records.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">
                          <button
                            className="hover:underline focus:outline-none"
                            onClick={() => setSelectedStudentId(r.student_id)}
                          >
                            {r.student_name}
                          </button>
                        </TableCell>
                        <TableCell>{r.class_name}</TableCell>
                        <TableCell>
                          {new Date(r.event_time).toLocaleString("uz")}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              r.event_type === "entry" ? "default" : "secondary"
                            }
                            className="text-xs"
                          >
                            {r.event_type === "entry" ? "Kirdi" : "Chiqdi"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {r.device_name ?? "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                {!isLoading && records.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="py-8 text-center text-muted-foreground"
                    >
                      Davomat yozuvlari topilmadi
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Jami: {pagination.total}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Oldingi
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= pagination.total_pages}
                  onClick={() => setPage(page + 1)}
                >
                  Keyingi
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Live feed + Group stats */}
      <div className="grid gap-4 lg:grid-cols-2">
        <LiveFeed classFilter={filters.class_name} />
        <GroupStats />
      </div>

      {/* Student side panel */}
      <StudentSidePanel
        studentId={selectedStudentId}
        onClose={() => setSelectedStudentId(null)}
      />
    </div>
  );
}
