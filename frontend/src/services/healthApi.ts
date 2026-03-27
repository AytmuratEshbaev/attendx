import api from "./api";

export interface HealthCheck {
  database: { status: string; type?: string; message?: string };
  redis: { status: string; used_memory?: string; message?: string };
  disk: { status: string; free_gb?: number; used_percent?: number };
  worker: { status: string; last_heartbeat_seconds_ago?: number };
  devices: { total?: number; online?: number; status?: string };
  data: { active_students?: number; today_events?: number; status?: string };
}

export interface DetailedHealth {
  status: "ok" | "warning" | "degraded";
  version: string;
  timestamp: string;
  uptime_seconds: number;
  checks: HealthCheck;
}

export const healthApi = {
  basic: () => fetch("/health").then((r) => r.json()),
  detailed: () =>
    api.get<{ success: boolean; data?: DetailedHealth }>("/health/detailed").catch(
      // Re-try without /api/v1 prefix (health is mounted at root)
      () => fetch("/health/detailed", {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}` },
      }).then((r) => r.json())
    ),
};
