import api from "./api";
import type {
  ApiResponse,
  PaginatedResponse,
  Webhook,
  WebhookLog,
} from "@/types";

export const webhooksApi = {
  list: () => api.get<ApiResponse<Webhook[]>>("/webhooks"),

  create: (data: { url: string; events: string[]; description?: string }) =>
    api.post<ApiResponse<Webhook>>("/webhooks", data),

  update: (
    id: string,
    data: Partial<{ url: string; events: string[]; is_active: boolean; description: string }>,
  ) => api.put<ApiResponse<Webhook>>(`/webhooks/${id}`, data),

  delete: (id: string) => api.delete(`/webhooks/${id}`),

  logs: (
    id: string,
    params?: { page?: number; per_page?: number; success?: boolean },
  ) =>
    api.get<PaginatedResponse<WebhookLog>>(`/webhooks/${id}/logs`, { params }),

  test: (id: string) => api.post(`/webhooks/${id}/test`),

  stats: () => api.get<ApiResponse<Record<string, unknown>>>("/webhooks/stats"),

  circuitBreaker: (id: string) =>
    api.get<ApiResponse<{ state: string; failure_count: number; last_failure_at: string | null }>>(
      `/webhooks/${id}/circuit-breaker`,
    ),

  resetCircuitBreaker: (id: string) =>
    api.post(`/webhooks/${id}/circuit-breaker/reset`),

  retry: (id: string) => api.post(`/webhooks/${id}/retry`),
};
