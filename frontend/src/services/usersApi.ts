import api from "./api";
import type { ApiResponse, PaginatedResponse, User } from "@/types";
import type { UserCreate, UserUpdate } from "@/types";

export const usersApi = {
  list: (params?: { page?: number; per_page?: number; role?: string }) =>
    api.get<PaginatedResponse<User>>("/users", { params }),

  get: (id: string) => api.get<ApiResponse<User>>(`/users/${id}`),

  create: (data: UserCreate) =>
    api.post<ApiResponse<User>>("/users", data),

  update: (id: string, data: UserUpdate) =>
    api.put<ApiResponse<User>>(`/users/${id}`, data),

  delete: (id: string) => api.delete(`/users/${id}`),
};
