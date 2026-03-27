import api from "./api";
import type { ApiResponse, Timetable, TimetableCreate, TimetableUpdate } from "@/types";

export const timetablesApi = {
  list: (timetable_type?: string) =>
    api.get<ApiResponse<Timetable[]>>("/timetables", {
      params: timetable_type ? { timetable_type } : undefined,
    }),

  get: (id: number) => api.get<ApiResponse<Timetable>>(`/timetables/${id}`),

  create: (data: TimetableCreate) =>
    api.post<ApiResponse<Timetable>>("/timetables", data),

  update: (id: number, data: TimetableUpdate) =>
    api.put<ApiResponse<Timetable>>(`/timetables/${id}`, data),

  delete: (id: number) => api.delete(`/timetables/${id}`),
};
