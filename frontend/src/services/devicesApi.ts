import api from "./api";
import type { ApiResponse, Device, DeviceCreate, DeviceHealth } from "@/types";

export const devicesApi = {
  list: () => api.get<ApiResponse<Device[]>>("/devices"),

  create: (data: DeviceCreate) =>
    api.post<ApiResponse<Device>>("/devices", data),

  update: (id: number, data: Partial<DeviceCreate>) =>
    api.put<ApiResponse<Device>>(`/devices/${id}`, data),

  delete: (id: number) => api.delete(`/devices/${id}`),

  sync: (id: number) => api.post(`/devices/${id}/sync`),

  health: (id: number) =>
    api.get<ApiResponse<DeviceHealth>>(`/devices/${id}/health`),

  importPersons: (id: number, categoryId?: number) =>
    api.post<ApiResponse<{ total: number; created: number; skipped: number; errors: string[] }>>(
      `/devices/${id}/import-persons`,
      null,
      { params: categoryId ? { category_id: categoryId } : {} }
    ),
};
