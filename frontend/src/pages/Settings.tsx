import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Loader2,
  Lock,
  User,
  Bell,
  Server,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  MessageCircle,
  Eye,
  EyeOff,
  ExternalLink,
  Database,
  Cpu,
  HardDrive,
  Activity,
  Clock,
  Copy,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { authApi } from "@/services/authApi";
import { getErrorMessage } from "@/services/api";
import { telegramApi } from "@/services/telegramApi";
import { useAuthStore } from "@/store/authStore";
import { PageHeader } from "@/components/common/PageHeader";
import { cn } from "@/lib/utils";

// ── Timed formatters ────────────────────────────────────────────────────────

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}k ${h}s`;
  if (h > 0) return `${h}s ${m}d`;
  return `${m}d`;
}

// ── Health status icon ───────────────────────────────────────────────────────

function StatusIcon({ status }: { status: string }) {
  if (status === "ok")
    return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  if (status === "warning")
    return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
  return <XCircle className="h-4 w-4 text-red-500" />;
}

// ── System Tab ───────────────────────────────────────────────────────────────

function SystemTab() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["health-detailed"],
    queryFn: async () => {
      // health/detailed is mounted outside /api/v1 — call directly
      const res = await fetch("/health/detailed", {
        headers: {
          Authorization: `Bearer ${useAuthStore.getState().accessToken ?? ""}`,
        },
      });
      if (!res.ok) throw new Error("Health check failed");
      return res.json();
    },
    refetchInterval: 30_000,
    retry: 1,
  });

  const health = data as {
    status: string;
    version: string;
    timestamp: string;
    uptime_seconds: number;
    checks: {
      database: { status: string; type?: string };
      redis: { status: string; used_memory?: string };
      disk: { status: string; free_gb?: number; used_percent?: number };
      worker: { status: string; last_heartbeat_seconds_ago?: number };
      devices: { total?: number; online?: number; status?: string };
      data: { active_students?: number; today_events?: number };
    };
  };

  const statusColor = {
    ok: "text-green-600 bg-green-50 border-green-200 dark:bg-green-950/40 dark:border-green-800",
    warning:
      "text-yellow-600 bg-yellow-50 border-yellow-200 dark:bg-yellow-950/40 dark:border-yellow-800",
    degraded:
      "text-red-600 bg-red-50 border-red-200 dark:bg-red-950/40 dark:border-red-800",
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              Tizim holati
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="gap-1.5"
            >
              <RefreshCw
                className={cn("h-3.5 w-3.5", isFetching && "animate-spin")}
              />
              Yangilash
            </Button>
          </div>
          <CardDescription>30 soniyada bir marta yangilanadi</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !health ? (
            <div className="flex flex-col items-center py-8 text-center">
              <XCircle className="mb-3 h-10 w-10 text-red-400" />
              <p className="text-sm text-muted-foreground">
                Tizim ma'lumotlarini yuklab bo'lmadi
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => refetch()}
              >
                Qayta urinish
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Overall status */}
              <div
                className={cn(
                  "flex items-center justify-between rounded-lg border px-4 py-3",
                  statusColor[health.status as keyof typeof statusColor] ??
                    statusColor.degraded,
                )}
              >
                <div>
                  <p className="font-semibold capitalize">
                    Holat:{" "}
                    {health.status === "ok"
                      ? "Yaxshi"
                      : health.status === "warning"
                        ? "Ogohlantirish"
                        : "Buzilgan"}
                  </p>
                  <p className="text-xs opacity-75">
                    Versiya {health.version} · Ishlash vaqti:{" "}
                    {formatUptime(health.uptime_seconds)}
                  </p>
                </div>
                <Activity className="h-6 w-6 opacity-60" />
              </div>

              {/* Check cards */}
              <div className="grid gap-3 sm:grid-cols-2">
                {/* Database */}
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <Database className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Ma'lumotlar bazasi</span>
                      <StatusIcon status={health.checks.database?.status} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {health.checks.database?.type ?? "PostgreSQL"}
                    </p>
                  </div>
                </div>

                {/* Redis */}
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <Cpu className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Redis</span>
                      <StatusIcon status={health.checks.redis?.status} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {health.checks.redis?.used_memory
                        ? `Xotira: ${health.checks.redis.used_memory}`
                        : "Ulangan"}
                    </p>
                  </div>
                </div>

                {/* Disk */}
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <HardDrive className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Disk</span>
                      <StatusIcon status={health.checks.disk?.status ?? "ok"} />
                    </div>
                    {health.checks.disk?.used_percent !== undefined ? (
                      <>
                        <Progress
                          value={health.checks.disk.used_percent}
                          className="mt-1.5 h-1.5"
                        />
                        <p className="mt-1 text-xs text-muted-foreground">
                          {health.checks.disk.used_percent}% foydalanilgan ·{" "}
                          {health.checks.disk.free_gb} GB bo'sh
                        </p>
                      </>
                    ) : (
                      <p className="text-xs text-muted-foreground">Noma'lum</p>
                    )}
                  </div>
                </div>

                {/* Worker */}
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <Activity className="mt-0.5 h-5 w-5 flex-shrink-0 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Worker</span>
                      <StatusIcon
                        status={
                          health.checks.worker?.status === "not_running"
                            ? "error"
                            : health.checks.worker?.status ?? "error"
                        }
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {health.checks.worker?.status === "not_running"
                        ? "Ishlamayapti"
                        : health.checks.worker?.last_heartbeat_seconds_ago !== undefined
                          ? `${health.checks.worker.last_heartbeat_seconds_ago}s oldin`
                          : "Noma'lum"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Data summary */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border bg-muted/30 p-3 text-center">
                  <p className="text-2xl font-bold">
                    {health.checks.data?.active_students ?? "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">Faol o'quvchilar</p>
                </div>
                <div className="rounded-lg border bg-muted/30 p-3 text-center">
                  <p className="text-2xl font-bold">
                    {health.checks.data?.today_events ?? "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">Bugungi hodisalar</p>
                </div>
                <div className="rounded-lg border bg-muted/30 p-3 text-center">
                  <p className="text-2xl font-bold">
                    {health.checks.devices?.online ?? 0}/
                    {health.checks.devices?.total ?? 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Online qurilmalar</p>
                </div>
                <div className="rounded-lg border bg-muted/30 p-3 text-center">
                  <p className="text-2xl font-bold text-muted-foreground text-sm font-normal mt-1">
                    {health.timestamp
                      ? new Date(health.timestamp).toLocaleTimeString("uz")
                      : "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">So'nggi yangilanish</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Notifications Tab ────────────────────────────────────────────────────────

function NotificationsTab() {
  const { data: statsRes, isLoading, refetch } = useQuery({
    queryKey: ["telegram-stats"],
    queryFn: () => telegramApi.stats(),
    retry: 1,
  });

  const stats = statsRes?.data?.data;

  const copyBotLink = () => {
    if (stats?.bot_username) {
      navigator.clipboard.writeText(`https://t.me/${stats.bot_username}`);
      toast.success("Havola nusxalandi");
    }
  };

  return (
    <div className="space-y-4">
      {/* Bot status card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-blue-500" />
            Telegram Bot
          </CardTitle>
          <CardDescription>
            Ota-onalar farzandlarining kelish/ketish xabarini Telegram orqali oladi
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : !stats ? (
            <div className="flex flex-col items-center py-6 text-center">
              <AlertTriangle className="mb-3 h-10 w-10 text-yellow-400" />
              <p className="text-sm font-medium">Bot ma'lumotlari yuklanmadi</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                Qayta urinish
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Bot configured status */}
              <div
                className={cn(
                  "flex items-center gap-3 rounded-lg border px-4 py-3",
                  stats.bot_configured
                    ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/40"
                    : "border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950/40",
                )}
              >
                {stats.bot_configured ? (
                  <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-500" />
                ) : (
                  <AlertTriangle className="h-5 w-5 flex-shrink-0 text-yellow-500" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-semibold">
                    {stats.bot_configured
                      ? "Bot sozlangan va ishlamoqda"
                      : "Bot sozlanmagan"}
                  </p>
                  {stats.bot_username && (
                    <p className="text-xs text-muted-foreground">
                      @{stats.bot_username}
                    </p>
                  )}
                </div>
                {stats.bot_username && (
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs"
                      onClick={copyBotLink}
                    >
                      <Copy className="h-3 w-3" />
                      Nusxalash
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-xs"
                      asChild
                    >
                      <a
                        href={`https://t.me/${stats.bot_username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Ochish
                      </a>
                    </Button>
                  </div>
                )}
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">{stats.active_subscriptions}</p>
                  <p className="text-xs text-muted-foreground">Faol obunalar</p>
                </div>
                <div className="rounded-lg border p-3 text-center">
                  <p className="text-2xl font-bold">{stats.unique_parents}</p>
                  <p className="text-xs text-muted-foreground">Ota-onalar</p>
                </div>
                <div className="rounded-lg border p-3 text-center col-span-2 sm:col-span-1">
                  <p className="text-2xl font-bold">{stats.coverage_percentage}%</p>
                  <p className="text-xs text-muted-foreground">Qamrov</p>
                </div>
              </div>

              {/* Coverage progress */}
              <div>
                <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
                  <span>
                    {stats.students_with_subscription} ta o'quvchi (
                    {stats.total_students} tadan)
                  </span>
                  <span>{stats.coverage_percentage}%</span>
                </div>
                <Progress value={stats.coverage_percentage} className="h-2" />
              </div>

              {/* Recent subscriptions */}
              {stats.recent_subscriptions.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                    So'nggi obunalar
                  </p>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {stats.recent_subscriptions.map((sub, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-md border px-3 py-2 text-xs"
                      >
                        <div>
                          <p className="font-medium">{sub.student_name}</p>
                          <p className="text-muted-foreground">
                            {sub.class_name} · {sub.phone}
                          </p>
                        </div>
                        <span className="text-muted-foreground">
                          {new Date(sub.subscribed_at).toLocaleDateString("uz")}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* How it works */}
              {!stats.bot_configured && (
                <div className="rounded-lg border border-dashed p-4">
                  <p className="mb-2 text-sm font-medium">Botni ulash uchun:</p>
                  <ol className="space-y-1.5 text-sm text-muted-foreground list-decimal list-inside">
                    <li>
                      @BotFather dan yangi bot yarating va tokenni oling
                    </li>
                    <li>
                      <code className="rounded bg-muted px-1 py-0.5 text-xs">
                        TELEGRAM_BOT_TOKEN
                      </code>{" "}
                      va{" "}
                      <code className="rounded bg-muted px-1 py-0.5 text-xs">
                        TELEGRAM_BOT_USERNAME
                      </code>{" "}
                      ni .env faylga kiriting
                    </li>
                    <li>Bot serviceni qayta ishga tushiring</li>
                    <li>Ota-onalar botga /start bosib ro'yxatdan o'tadi</li>
                  </ol>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Main Settings Page ───────────────────────────────────────────────────────

export default function Settings() {
  const user = useAuthStore((s) => s.user);
  const [activeTab, setActiveTab] = useState("general");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const isAdmin = user?.role === "super_admin" || user?.role === "admin";

  const passwordMutation = useMutation({
    mutationFn: () =>
      authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      toast.success("Parol muvaffaqiyatli o'zgartirildi");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleSubmit = () => {
    if (newPassword !== confirmPassword) {
      toast.error("Yangi parollar mos kelmaydi");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("Parol kamida 6 ta belgidan iborat bo'lishi kerak");
      return;
    }
    passwordMutation.mutate();
  };

  const roleLabels: Record<string, string> = {
    super_admin: "Super Admin",
    admin: "Admin",
    teacher: "O'qituvchi",
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Sozlamalar" description="Profil va tizim sozlamalari" />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="general" className="gap-1.5">
            <User className="h-4 w-4" />
            Umumiy
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-1.5">
            <Lock className="h-4 w-4" />
            Xavfsizlik
          </TabsTrigger>
          {isAdmin && (
            <>
              <TabsTrigger value="notifications" className="gap-1.5">
                <Bell className="h-4 w-4" />
                Bildirishnomalar
              </TabsTrigger>
              <TabsTrigger value="system" className="gap-1.5">
                <Server className="h-4 w-4" />
                Tizim
              </TabsTrigger>
            </>
          )}
        </TabsList>

        {/* General */}
        <TabsContent value="general">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Profil
              </CardTitle>
              <CardDescription>Joriy foydalanuvchi ma'lumotlari</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="space-y-3">
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                  <dt className="text-sm text-muted-foreground">Foydalanuvchi nomi</dt>
                  <dd className="text-sm font-medium">{user?.username ?? "—"}</dd>
                </div>
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                  <dt className="text-sm text-muted-foreground">Email</dt>
                  <dd className="text-sm font-medium">{user?.email ?? "—"}</dd>
                </div>
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                  <dt className="text-sm text-muted-foreground">Rol</dt>
                  <dd>
                    <Badge variant="outline">
                      {roleLabels[user?.role ?? ""] ?? user?.role}
                    </Badge>
                  </dd>
                </div>
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                  <dt className="text-sm text-muted-foreground">So'nggi kirish</dt>
                  <dd className="text-sm font-medium">
                    {user?.last_login_at
                      ? new Date(user.last_login_at).toLocaleString("uz")
                      : "—"}
                  </dd>
                </div>
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                  <dt className="text-sm text-muted-foreground">Holat</dt>
                  <dd>
                    <Badge variant={user?.is_active ? "default" : "destructive"}>
                      {user?.is_active ? "Faol" : "Faol emas"}
                    </Badge>
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Parolni o'zgartirish
              </CardTitle>
              <CardDescription>
                Kamida 6 ta belgi. Kuchli parol ishlatishingiz tavsiya etiladi.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Joriy parol</Label>
                <div className="relative">
                  <Input
                    type={showOld ? "text" : "password"}
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    placeholder="Joriy parolni kiriting"
                    className="pr-10"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowOld((v) => !v)}
                  >
                    {showOld ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Yangi parol</Label>
                <div className="relative">
                  <Input
                    type={showNew ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Yangi parolni kiriting"
                    className="pr-10"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowNew((v) => !v)}
                  >
                    {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {newPassword.length > 0 && newPassword.length < 6 && (
                  <p className="text-xs text-destructive">
                    Parol kamida 6 ta belgidan iborat bo'lishi kerak
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Yangi parolni tasdiqlang</Label>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Yangi parolni qayta kiriting"
                />
                {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                  <p className="text-xs text-destructive">Parollar mos kelmaydi</p>
                )}
              </div>
              <Button
                onClick={handleSubmit}
                disabled={
                  passwordMutation.isPending ||
                  !oldPassword ||
                  !newPassword ||
                  !confirmPassword ||
                  newPassword !== confirmPassword ||
                  newPassword.length < 6
                }
                className="w-full sm:w-auto"
              >
                {passwordMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Lock className="mr-2 h-4 w-4" />
                )}
                Parolni o'zgartirish
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications */}
        {isAdmin && (
          <TabsContent value="notifications">
            <NotificationsTab />
          </TabsContent>
        )}

        {/* System */}
        {isAdmin && (
          <TabsContent value="system">
            <SystemTab />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
