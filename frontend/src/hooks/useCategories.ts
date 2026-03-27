import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { categoriesApi } from "@/services/categoriesApi";
import { getErrorMessage } from "@/services/api";
import type { CategoryCreate, CategoryUpdate } from "@/types";

export function useCategories(parentId?: number | null) {
  return useQuery({
    queryKey: ["categories", parentId],
    queryFn: () => categoriesApi.list(parentId),
    staleTime: 2 * 60 * 1000,
  });
}

export function useTopLevelCategories() {
  return useQuery({
    queryKey: ["categories", 0],
    queryFn: () => categoriesApi.list(0),
    staleTime: 2 * 60 * 1000,
  });
}

export function useChildCategories(parentId: number) {
  return useQuery({
    queryKey: ["categories", parentId],
    queryFn: () => categoriesApi.list(parentId),
    staleTime: 2 * 60 * 1000,
    enabled: !!parentId,
  });
}

export function useCategoryStats(id: number) {
  return useQuery({
    queryKey: ["category-stats", id],
    queryFn: () => categoriesApi.stats(id),
    staleTime: 60_000,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoryCreate) => categoriesApi.create(data),
    onSuccess: () => {
      toast.success("Kategoriya yaratildi");
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CategoryUpdate }) =>
      categoriesApi.update(id, data),
    onSuccess: () => {
      toast.success("Kategoriya yangilandi");
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => categoriesApi.delete(id),
    onSuccess: () => {
      toast.warning("Kategoriya o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}
