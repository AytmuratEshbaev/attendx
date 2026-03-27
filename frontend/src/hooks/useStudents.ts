import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { studentsApi } from "@/services/studentsApi";
import { getErrorMessage } from "@/services/api";
import type { StudentCreate, StudentUpdate } from "@/types";

export function useStudents(params: {
  page?: number;
  per_page?: number;
  class_name?: string;
  search?: string;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: ["students", params],
    queryFn: () => studentsApi.list(params),
  });
}

export function useStudent(id: string | undefined) {
  return useQuery({
    queryKey: ["student", id],
    queryFn: () => studentsApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.create(data),
    onSuccess: () => {
      toast.success("O'quvchi yaratildi");
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateStudent(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: StudentUpdate) => studentsApi.update(id, data),
    onSuccess: () => {
      toast.success("O'quvchi yangilandi");
      queryClient.invalidateQueries({ queryKey: ["student", id] });
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => studentsApi.delete(id),
    onSuccess: () => {
      toast.success("O'quvchi o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useImportStudents() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => studentsApi.import(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}
