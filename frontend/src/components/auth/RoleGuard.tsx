import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { toast } from "sonner";

interface RoleGuardProps {
  roles: string[];
}

export function RoleGuard({ roles }: RoleGuardProps) {
  const user = useAuthStore((s) => s.user);

  if (!user || !roles.includes(user.role)) {
    toast.error("Ruxsat yo'q");
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
