import { useQuery } from "@tanstack/react-query";
import { attendanceApi } from "@/services/attendanceApi";

export function useAttendanceList(params: {
  page?: number;
  per_page?: number;
  date_from?: string;
  date_to?: string;
  class_name?: string;
  event_type?: string;
}) {
  return useQuery({
    queryKey: ["attendance", params],
    queryFn: () => attendanceApi.list(params),
  });
}

export function useAttendanceStats(date?: string, className?: string) {
  return useQuery({
    queryKey: ["attendance-stats", date, className],
    queryFn: () => attendanceApi.stats(date, className),
    refetchInterval: 30_000,
  });
}

export function useWeeklyAttendance(startDate?: string, className?: string) {
  return useQuery({
    queryKey: ["attendance-weekly", startDate, className],
    queryFn: () => attendanceApi.weekly(startDate, className),
  });
}

export function useTodayAttendance(className?: string) {
  return useQuery({
    queryKey: ["attendance-today", className],
    queryFn: () => attendanceApi.today(className),
    refetchInterval: 10_000,
  });
}

export function useRecentAttendance(limit = 100) {
  return useQuery({
    queryKey: ["attendance-recent", limit],
    queryFn: () => attendanceApi.recent(limit),
    refetchInterval: 10_000,
  });
}

export function useStudentAttendance(
  studentId: string | undefined,
  params?: { date_from?: string; date_to?: string },
) {
  return useQuery({
    queryKey: ["student-attendance", studentId, params],
    queryFn: () => attendanceApi.studentHistory(studentId!, params),
    enabled: !!studentId,
  });
}
