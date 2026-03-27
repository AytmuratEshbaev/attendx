import { useQuery } from "@tanstack/react-query";
import {
  Users,
  UserCheck,
  UserX,
  TrendingUp,
  TrendingDown,
  Minus,
  Loader2,
  Wifi,
  WifiOff,
  Clock,
  AlertTriangle,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { attendanceApi } from "@/services/attendanceApi";
import { devicesApi } from "@/services/devicesApi";
import type { AttendanceRecord, AttendanceStats, Device } from "@/types";
import { cn } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { useNavigate } from "react-router-dom";

const COLOR_MAP = {
  blue: "bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
  green: "bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400",
  red: "bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400",
  orange: "bg-orange-100 text-orange-600 dark:bg-orange-950 dark:text-orange-400",
} as const;

const PIE_COLORS = [
  "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
  "#14b8a6", "#a855f7", "#f97316", "#06b6d4",
];

type TrendDirection = "up" | "down" | "neutral";
interface Trend { direction: TrendDirection; text: string }

function computeTrend(today: number, yesterday: number): Trend {
  if (yesterday === 0) return { direction: "neutral", text: "Kechagi ma'lumot yo'q" };
  const diff = today - yesterday;
  const pct = Math.abs(Math.round((diff / yesterday) * 100));
  if (diff > 0) return { direction: "up", text: `+${pct}% kechagiga nisbatan` };
  if (diff < 0) return { direction: "down", text: `-${pct}% kechagiga nisbatan` };
  return { direction: "neutral", text: "O'zgarish yo'q" };
}

function StatCard({
  title, value, icon: Icon, loading, color = "blue", trend,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  loading?: boolean;
  color?: keyof typeof COLOR_MAP;
  trend?: Trend;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={cn("rounded-md p-2", COLOR_MAP[color])}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <>
            <div className="text-2xl font-bold">{value}</div>
            {trend && (
              <div className={cn(
                "mt-1 flex items-center gap-1 text-xs",
                trend.direction === "up" && "text-green-600",
                trend.direction === "down" && "text-red-500",
                trend.direction === "neutral" && "text-muted-foreground",
              )}>
                {trend.direction === "up" && <TrendingUp className="h-3 w-3" />}
                {trend.direction === "down" && <TrendingDown className="h-3 w-3" />}
                {trend.direction === "neutral" && <Minus className="h-3 w-3" />}
                {trend.text}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function isDeviceOnline(device: Device): boolean {
  if (!device.is_active || !device.last_online_at) return false;
  return Date.now() - new Date(device.last_online_at).getTime() < 2 * 60 * 1000;
}

// Alert card for low attendance classes
function LowAttendanceAlert({
  byClass,
}: {
  byClass: AttendanceStats["by_class"];
}) {
  const navigate = useNavigate();
  const lowClasses = Object.entries(byClass)
    .filter(([, d]) => d.percentage < 70 && d.total > 0)
    .sort((a, b) => a[1].percentage - b[1].percentage)
    .slice(0, 5);

  if (lowClasses.length === 0) return null;

  return (
    <Card className="border-yellow-200 bg-yellow-50/50 dark:border-yellow-800 dark:bg-yellow-950/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-yellow-700 dark:text-yellow-400">
          <AlertTriangle className="h-4 w-4" />
          Past davomat ({lowClasses.length} sinf)
        </CardTitle>
        <CardDescription>70% dan kam davomat bo'lgan sinflar</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {lowClasses.map(([name, d]) => (
            <div
              key={name}
              className="flex items-center justify-between rounded-md border border-yellow-200 bg-white px-3 py-2 dark:border-yellow-800 dark:bg-card cursor-pointer hover:shadow-sm transition-shadow"
              onClick={() => navigate(`/attendance?class=${encodeURIComponent(name)}`)}
            >
              <span className="text-sm font-medium">{name}</span>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span>{d.present}/{d.total}</span>
                <Badge
                  variant={d.percentage < 50 ? "destructive" : "secondary"}
                  className="w-14 justify-center"
                >
                  {Math.round(d.percentage)}%
                </Badge>
              </div>
            </div>
          ))}
        </div>
        <Button
          variant="link"
          size="sm"
          className="mt-2 h-auto p-0 text-yellow-700 dark:text-yellow-400"
          onClick={() => navigate("/attendance")}
        >
          Barchasi →
        </Button>
      </CardContent>
    </Card>
  );
}

// Offline devices alert
function OfflineDevicesAlert({ devices }: { devices: Device[] }) {
  const navigate = useNavigate();
  const offline = devices.filter((d) => d.is_active && !isDeviceOnline(d));

  if (offline.length === 0) return null;

  return (
    <Card className="border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-red-700 dark:text-red-400">
          <WifiOff className="h-4 w-4" />
          Offline qurilmalar ({offline.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {offline.map((d) => (
            <div
              key={d.id}
              className="flex items-center justify-between rounded-md border border-red-200 bg-white px-3 py-2 dark:border-red-800 dark:bg-card"
            >
              <span className="text-sm font-medium">{d.name}</span>
              <span className="text-xs text-muted-foreground">{d.ip_address}</span>
            </div>
          ))}
        </div>
        <Button
          variant="link"
          size="sm"
          className="mt-2 h-auto p-0 text-red-700 dark:text-red-400"
          onClick={() => navigate("/devices")}
        >
          Qurilmalarni boshqarish →
        </Button>
      </CardContent>
    </Card>
  );
}

// Day label for weekly chart
const DAY_UZ: Record<string, string> = {
  Mon: "Du", Tue: "Se", Wed: "Ch", Thu: "Pa",
  Fri: "Ju", Sat: "Sh", Sun: "Ya",
};

function formatChartDate(dateStr: string): string {
  const d = new Date(dateStr);
  const dayName = d.toLocaleDateString("en", { weekday: "short" });
  return DAY_UZ[dayName] ?? dayName;
}

export default function Analytics() {
  const yesterdayStr = new Date(Date.now() - 86400000).toISOString().split("T")[0];

  const { data: statsRes, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ["attendance-stats"],
    queryFn: () => attendanceApi.stats(),
    refetchInterval: 30_000,
  });

  const { data: yesterdayRes } = useQuery({
    queryKey: ["attendance-stats", yesterdayStr],
    queryFn: () => attendanceApi.stats(yesterdayStr),
  });

  const { data: weeklyRes, isLoading: weeklyLoading } = useQuery({
    queryKey: ["attendance-weekly"],
    queryFn: () => attendanceApi.weekly(),
  });

  const { data: todayRes, isLoading: todayLoading, refetch: refetchToday } = useQuery({
    queryKey: ["attendance-today"],
    queryFn: () => attendanceApi.today(),
    refetchInterval: 10_000,
  });

  const { data: devicesRes, isLoading: devicesLoading } = useQuery({
    queryKey: ["devices"],
    queryFn: () => devicesApi.list(),
    refetchInterval: 30_000,
  });

  const stats: AttendanceStats | undefined = statsRes?.data?.data;
  const yesterdayStats: AttendanceStats | undefined = yesterdayRes?.data?.data;
  const weekly = (weeklyRes?.data?.data ?? []).map((d) => ({
    ...d,
    label: formatChartDate(d.date),
  }));
  const todayEvents: AttendanceRecord[] = (todayRes?.data?.data ?? []).slice(0, 20);
  const devices: Device[] = devicesRes?.data?.data ?? [];

  const pieData = stats?.by_class
    ? Object.entries(stats.by_class).map(([name, d]) => ({
        name,
        value: d.present,
        total: d.total,
      }))
    : [];

  const onlineCount = devices.filter(isDeviceOnline).length;

  const presentTrend = yesterdayStats
    ? computeTrend(stats?.present_today ?? 0, yesterdayStats.present_today)
    : undefined;
  const absentTrend = yesterdayStats
    ? computeTrend(stats?.absent_today ?? 0, yesterdayStats.absent_today)
    : undefined;
  const pctTrend = yesterdayStats
    ? computeTrend(stats?.attendance_percentage ?? 0, yesterdayStats.attendance_percentage)
    : undefined;

  const now = new Date();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Bosh sahifa</h1>
          <p className="text-muted-foreground">
            {now.toLocaleDateString("uz-UZ", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => {
            refetchStats();
            refetchToday();
          }}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Yangilash
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Jami o'quvchilar"
          value={stats?.total_students ?? 0}
          icon={Users}
          color="blue"
          loading={statsLoading}
        />
        <StatCard
          title="Bugun keldi"
          value={stats?.present_today ?? 0}
          icon={UserCheck}
          color="green"
          loading={statsLoading}
          trend={presentTrend}
        />
        <StatCard
          title="Bugun kelmadi"
          value={stats?.absent_today ?? 0}
          icon={UserX}
          color="red"
          loading={statsLoading}
          trend={absentTrend}
        />
        <StatCard
          title="Davomat foizi"
          value={`${stats?.attendance_percentage ?? 0}%`}
          icon={TrendingUp}
          color="orange"
          loading={statsLoading}
          trend={pctTrend}
        />
      </div>

      {/* Alert cards (only shown when there are issues) */}
      {(stats?.by_class || devices.length > 0) && (
        <div className="grid gap-4 lg:grid-cols-2">
          {stats?.by_class && <LowAttendanceAlert byClass={stats.by_class} />}
          {devices.length > 0 && <OfflineDevicesAlert devices={devices} />}
        </div>
      )}

      {/* Quick actions */}
      <QuickActions />

      {/* Weekly chart + Device status */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-muted-foreground" />
                  Haftalik davomat
                </CardTitle>
                <CardDescription>So'nggi 7 kunlik statistika</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {weeklyLoading ? (
              <div className="flex h-[280px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : weekly.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={weekly} barGap={2}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="label" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    formatter={(v, name) => [
                      v,
                      name === "present" ? "Keldi" : "Kelmadi",
                    ]}
                    labelFormatter={(label) => `${label} kuni`}
                  />
                  <Bar dataKey="present" name="Keldi" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="absent" name="Kelmadi" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[280px] items-center justify-center text-muted-foreground">
                Ma'lumot mavjud emas
              </div>
            )}
          </CardContent>
        </Card>

        {/* Device status panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-4 w-4 text-muted-foreground" />
              Qurilmalar
            </CardTitle>
            <CardDescription>
              {onlineCount}/{devices.length} online
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {devicesLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))
            ) : devices.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Qurilmalar yo'q
              </p>
            ) : (
              devices.map((device) => {
                const online = isDeviceOnline(device);
                return (
                  <div
                    key={device.id}
                    className="flex items-center justify-between rounded-lg border p-2.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "h-2 w-2 rounded-full flex-shrink-0",
                        online ? "bg-green-500" : "bg-red-400",
                      )} />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{device.name}</p>
                        <p className="text-xs text-muted-foreground">{device.ip_address}</p>
                      </div>
                    </div>
                    <Badge
                      variant={online ? "default" : "destructive"}
                      className="gap-1 flex-shrink-0"
                    >
                      {online ? (
                        <Wifi className="h-3 w-3" />
                      ) : (
                        <WifiOff className="h-3 w-3" />
                      )}
                      {online ? "Online" : "Offline"}
                    </Badge>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      {/* Per-class chart + Recent events */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Donut chart by class */}
        <Card>
          <CardHeader>
            <CardTitle>Sinf bo'yicha davomat</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="flex h-[280px] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : pieData.length > 0 ? (
              <div className="space-y-4">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {pieData.map((_, index) => (
                        <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v, _n, props) => [
                        `${v}/${props.payload.total}`,
                        "Keldi",
                      ]}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 max-h-36 overflow-y-auto">
                  {pieData.map((cls, i) => (
                    <div key={cls.name} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2 w-2 rounded-full flex-shrink-0"
                          style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
                        />
                        <span className="truncate">{cls.name}</span>
                      </div>
                      <span className="text-muted-foreground flex-shrink-0 ml-2">
                        {cls.value}/{cls.total}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex h-[280px] items-center justify-center text-muted-foreground">
                Ma'lumot mavjud emas
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent events feed */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  So'nggi hodisalar
                  <span className="flex items-center gap-1 text-xs font-normal text-green-600">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
                    Jonli
                  </span>
                </CardTitle>
                <CardDescription>10 soniyada bir yangilanadi</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {todayLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : todayEvents.length === 0 ? (
              <div className="flex h-48 items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <Clock className="mx-auto mb-2 h-8 w-8 opacity-30" />
                  <p className="text-sm">Bugun hodisalar yo'q</p>
                </div>
              </div>
            ) : (
              <div className="max-h-[320px] space-y-1.5 overflow-y-auto pr-1">
                {todayEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between rounded-lg border p-2.5"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Clock className="h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">{event.student_name}</p>
                        <p className="text-xs text-muted-foreground">{event.class_name}</p>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right ml-2">
                      <Badge
                        variant={event.event_type === "entry" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {event.event_type === "entry" ? "Kirdi" : "Chiqdi"}
                      </Badge>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {new Date(event.event_time).toLocaleTimeString("uz", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
