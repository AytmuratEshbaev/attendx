import api from "./api";
import type { ApiResponse } from "@/types";

export interface TelegramStats {
  bot_username: string | null;
  bot_configured: boolean;
  total_subscriptions: number;
  active_subscriptions: number;
  unique_parents: number;
  students_with_subscription: number;
  total_students: number;
  coverage_percentage: number;
  recent_subscriptions: {
    chat_id: number;
    phone: string;
    student_name: string;
    class_name: string;
    subscribed_at: string;
  }[];
}

export const telegramApi = {
  stats: () => api.get<ApiResponse<TelegramStats>>("/telegram/stats"),
  unsubscribe: (chatId: number) =>
    api.delete<ApiResponse<{ deactivated: number }>>(`/telegram/subscriptions/${chatId}`),
};
