import api from "./api";
import type { ApiResponse, Category, CategoryCreate, CategoryUpdate } from "@/types";

export const categoriesApi = {
  list: (parentId?: number | null) =>
    api.get<ApiResponse<Category[]>>("/categories", {
      params: parentId !== undefined ? { parent_id: parentId } : {},
    }),

  create: (data: CategoryCreate) =>
    api.post<ApiResponse<Category>>("/categories", data),

  update: (id: number, data: CategoryUpdate) =>
    api.put<ApiResponse<Category>>(`/categories/${id}`, data),

  delete: (id: number) =>
    api.delete<ApiResponse<{ message: string }>>(`/categories/${id}`),

  stats: (id: number) =>
    api.get<ApiResponse<{ total: number; active: number; children: number }>>(
      `/categories/${id}/stats`
    ),
};
