import api from "./api";
import type {
  ApiResponse,
  AccessGroup,
  AccessGroupCreate,
  AccessGroupUpdate,
  AccessGroupMembership,
  SyncResult,
} from "@/types";

export const accessGroupsApi = {
  list: () => api.get<ApiResponse<AccessGroup[]>>("/access-groups"),

  get: (id: number) => api.get<ApiResponse<AccessGroup>>(`/access-groups/${id}`),

  create: (data: AccessGroupCreate) =>
    api.post<ApiResponse<AccessGroup>>("/access-groups", data),

  update: (id: number, data: AccessGroupUpdate) =>
    api.put<ApiResponse<AccessGroup>>(`/access-groups/${id}`, data),

  delete: (id: number) => api.delete(`/access-groups/${id}`),

  addDevice: (groupId: number, deviceId: number) =>
    api.post<ApiResponse<AccessGroup>>(
      `/access-groups/${groupId}/devices/${deviceId}`,
    ),

  removeDevice: (groupId: number, deviceId: number) =>
    api.delete<ApiResponse<AccessGroup>>(
      `/access-groups/${groupId}/devices/${deviceId}`,
    ),

  addStudent: (groupId: number, studentId: string) =>
    api.post<ApiResponse<AccessGroupMembership>>(
      `/access-groups/${groupId}/students/${studentId}`,
    ),

  removeStudent: (groupId: number, studentId: string) =>
    api.delete(`/access-groups/${groupId}/students/${studentId}`),

  retryStudentSync: (groupId: number, studentId: string) =>
    api.post<ApiResponse<AccessGroupMembership>>(
      `/access-groups/${groupId}/students/${studentId}/sync`,
    ),

  addCategory: (groupId: number, categoryId: number) =>
    api.post<ApiResponse<{ added: number; skipped: number }>>(
      `/access-groups/${groupId}/categories/${categoryId}`,
    ),

  sync: (groupId: number) =>
    api.post<ApiResponse<SyncResult>>(`/access-groups/${groupId}/sync`),
};
