import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { timetablesApi } from "@/services/timetablesApi";
import { getErrorMessage } from "@/services/api";
import type { TimetableCreate, TimetableUpdate } from "@/types";

export function useTimetables(timetableType?: string) {
  return useQuery({
    queryKey: ["timetables", timetableType ?? "all"],
    queryFn: () => timetablesApi.list(timetableType),
  });
}

export function useTimetable(id: number | null) {
  return useQuery({
    queryKey: ["timetables", id],
    queryFn: () => timetablesApi.get(id!),
    enabled: id !== null,
  });
}

export function useCreateTimetable() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TimetableCreate) => timetablesApi.create(data),
    onSuccess: () => {
      toast.success("Jadval yaratildi");
      qc.invalidateQueries({ queryKey: ["timetables"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateTimetable() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: TimetableUpdate }) =>
      timetablesApi.update(id, data),
    onSuccess: () => {
      toast.success("Jadval yangilandi");
      qc.invalidateQueries({ queryKey: ["timetables"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteTimetable() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => timetablesApi.delete(id),
    onSuccess: () => {
      toast.success("Jadval o'chirildi");
      qc.invalidateQueries({ queryKey: ["timetables"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}
