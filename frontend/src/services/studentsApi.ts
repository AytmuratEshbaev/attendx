import api from "./api";
import type {
  ApiResponse,
  PaginatedResponse,
  Student,
  StudentCreate,
  StudentImportResult,
  StudentUpdate,
} from "@/types";

export const studentsApi = {
  list: (params: {
    page?: number;
    per_page?: number;
    class_name?: string;
    category_id?: number;
    no_category?: boolean;
    search?: string;
    sort?: string;
    is_active?: boolean;
  }) => api.get<PaginatedResponse<Student>>("/students", { params }),

  get: (id: string) => api.get<ApiResponse<Student>>(`/students/${id}`),

  create: (data: StudentCreate) =>
    api.post<ApiResponse<Student>>("/students", data),

  update: (id: string, data: StudentUpdate) =>
    api.put<ApiResponse<Student>>(`/students/${id}`, data),

  delete: (id: string) => api.delete(`/students/${id}`),

  uploadFace: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ApiResponse<Student>>(`/students/${id}/face`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  import: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ApiResponse<StudentImportResult>>(
      "/students/import",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
  },

  export: (params?: { class_name?: string; format?: string; category_id?: number }) =>
    api.get("/students/export", { params, responseType: "blob" }),

  classes: () => api.get<ApiResponse<string[]>>("/students/classes"),
};
