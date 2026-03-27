import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/services/authApi";
import { Loader2 } from "lucide-react";

export function ProtectedRoute() {
  const { isAuthenticated, user, setUser, logout } = useAuthStore();
  const [checking, setChecking] = useState(!user && isAuthenticated);
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated && !user) {
      authApi
        .getMe()
        .then((res) => setUser(res.data.data))
        .catch(() => logout())
        .finally(() => setChecking(false));
    }
  }, [isAuthenticated, user, setUser, logout]);

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return <Outlet />;
}
