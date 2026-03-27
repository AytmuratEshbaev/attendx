import api from "./api";
import type { ApiResponse, LoginRequest, TokenResponse, User } from "@/types";

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<ApiResponse<TokenResponse>>("/auth/login", data),

  refresh: (refreshToken: string) =>
    api.post<ApiResponse<TokenResponse>>("/auth/refresh", {
      refresh_token: refreshToken,
    }),

  logout: () => api.post("/auth/logout"),

  getMe: () => api.get<ApiResponse<User>>("/auth/me"),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post("/auth/change-password", data),
};
