import api from "./api";
import type {
  ApiResponse,
  AttendanceRecord,
  AttendanceStats,
  DailyAttendance,
  DeviceLiveEvent,
  PaginatedResponse,
} from "@/types";

export const attendanceApi = {
  list: (params: {
    page?: number;
    per_page?: number;
    date_from?: string;
    date_to?: string;
    class_name?: string;
    event_type?: string;
  }) => api.get<PaginatedResponse<AttendanceRecord>>("/attendance", { params }),

  recent: (limit = 100) =>
    api.get<ApiResponse<AttendanceRecord[]>>("/attendance/recent", {
      params: { limit },
    }),

  deviceLive: (hours = 24, limit = 100) =>
    api.get<ApiResponse<DeviceLiveEvent[]>>("/attendance/device-live", {
      params: { hours, limit },
    }),

  today: (className?: string) =>
    api.get<ApiResponse<AttendanceRecord[]>>("/attendance/today", {
      params: { class_name: className },
    }),

  stats: (date?: string, className?: string) =>
    api.get<ApiResponse<AttendanceStats>>("/attendance/stats", {
      params: { date, class_name: className },
    }),

  weekly: (startDate?: string, className?: string) =>
    api.get<ApiResponse<DailyAttendance[]>>("/attendance/weekly", {
      params: { start_date: startDate, class_name: className },
    }),

  report: (params: {
    date_from: string;
    date_to: string;
    class_name?: string;
    format?: string;
  }) => api.get("/attendance/report", { params, responseType: "blob" }),

  studentHistory: (
    studentId: string,
    params?: { date_from?: string; date_to?: string },
  ) =>
    api.get<ApiResponse<{
      student: unknown;
      records: AttendanceRecord[];
      stats: { total_days: number; present_days: number; percentage: number };
    }>>(
      `/attendance/student/${studentId}`,
      { params },
    ),
};
