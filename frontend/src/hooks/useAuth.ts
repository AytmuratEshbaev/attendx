import { useQuery, useMutation } from "@tanstack/react-query";
import { authApi } from "@/services/authApi";
import { getErrorMessage } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";
import type { LoginRequest } from "@/types";

export function useLogin() {
  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onError: (err) => toast.error(getErrorMessage(err)),
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      logout();
      window.location.href = "/login";
    },
  });
}

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["auth-me"],
    queryFn: () => authApi.getMe(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}
