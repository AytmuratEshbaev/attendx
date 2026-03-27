import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Members from "@/pages/Members";
import StudentDetail from "@/pages/StudentDetail";
import Attendance from "@/pages/Attendance";
import Devices from "@/pages/Devices";
import Timetables from "@/pages/Timetables";
import AccessGroups from "@/pages/AccessGroups";
import AccessGroupDetail from "@/pages/AccessGroupDetail";
import Webhooks from "@/pages/Webhooks";
import Reports from "@/pages/Reports";
import Settings from "@/pages/Settings";
import Users from "@/pages/Users";
import ImportPersons from "@/pages/ImportPersons";
import Analytics from "@/pages/Analytics";
import NotFound from "@/pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
          </Route>

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/students" element={<Members />} />
              <Route path="/students/category/:categoryId" element={<Members />} />
              <Route path="/students/:id" element={<StudentDetail />} />
              <Route path="/attendance" element={<Attendance />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />

              {/* Admin-only routes */}
              <Route
                element={
                  <RoleGuard roles={["super_admin", "admin"]} />
                }
              >
                <Route path="/devices" element={<Devices />} />
                <Route path="/timetables" element={<Timetables />} />
                <Route path="/access-groups" element={<AccessGroups />} />
                <Route path="/access-groups/:id" element={<AccessGroupDetail />} />
                <Route path="/webhooks" element={<Webhooks />} />
                <Route path="/import-persons" element={<ImportPersons />} />
                <Route path="/analytics" element={<Analytics />} />
              </Route>

              {/* Super admin only */}
              <Route
                element={<RoleGuard roles={["super_admin"]} />}
              >
                <Route path="/users" element={<Users />} />
              </Route>

              {/* 404 inside dashboard */}
              <Route path="*" element={<NotFound />} />
            </Route>
          </Route>
        </Routes>
        <Toaster richColors position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
