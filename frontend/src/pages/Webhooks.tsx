import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Plus,
  MoreHorizontal,
  Trash2,
  TestTube,
  Loader2,
  Eye,
  ShieldAlert,
  RotateCcw,
  Activity,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { webhooksApi } from "@/services/webhooksApi";
import { getErrorMessage } from "@/services/api";
import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import type { Webhook } from "@/types";

const EVENT_OPTIONS = [
  "attendance.entry",
  "attendance.exit",
  "student.created",
  "student.updated",
  "student.deleted",
  "device.online",
  "device.offline",
  "face.registered",
];

export default function Webhooks() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [logsWebhookId, setLogsWebhookId] = useState<string | null>(null);
  const [cbWebhook, setCbWebhook] = useState<Webhook | null>(null);
  const [deleteWebhook, setDeleteWebhook] = useState<Webhook | null>(null);
  const [form, setForm] = useState({
    url: "",
    events: [] as string[],
    description: "",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["webhooks"],
    queryFn: () => webhooksApi.list(),
  });

  const { data: statsData } = useQuery({
    queryKey: ["webhook-stats"],
    queryFn: () => webhooksApi.stats(),
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ["webhook-logs", logsWebhookId],
    queryFn: () => webhooksApi.logs(logsWebhookId!, { per_page: 20 }),
    enabled: !!logsWebhookId,
  });

  const { data: cbData, isLoading: cbLoading } = useQuery({
    queryKey: ["webhook-cb", cbWebhook?.id],
    queryFn: () => webhooksApi.circuitBreaker(cbWebhook!.id),
    enabled: !!cbWebhook,
  });

  const createMutation = useMutation({
    mutationFn: (data: { url: string; events: string[]; description?: string }) =>
      webhooksApi.create(data),
    onSuccess: () => {
      toast.success("Webhook yaratildi");
      setCreateOpen(false);
      setForm({ url: "", events: [], description: "" });
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.delete(id),
    onSuccess: () => {
      toast.success("Webhook o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.test(id),
    onSuccess: () => toast.success("Test webhook yuborildi"),
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const resetCbMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.resetCircuitBreaker(id),
    onSuccess: () => {
      toast.success("Circuit breaker tiklandi");
      queryClient.invalidateQueries({ queryKey: ["webhook-cb", cbWebhook?.id] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const toggleEvent = (event: string) => {
    setForm((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }));
  };

  const webhooks = data?.data?.data ?? [];
  const logs = logsData?.data?.data ?? [];
  const stats = statsData?.data?.data as Record<string, unknown> | undefined;
  const cbState = cbData?.data?.data;

  const CB_STATE_COLORS: Record<string, string> = {
    closed: "bg-green-500",
    open: "bg-red-500",
    half_open: "bg-yellow-500",
  };

  const CB_STATE_LABELS: Record<string, string> = {
    closed: "Yopiq",
    open: "Ochiq",
    half_open: "Yarim ochiq",
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Webhooklar"
        description="Tashqi xizmatlarga hodisa bildirnomalari"
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Yangi webhook
          </Button>
        }
      />

      {/* Stats cards */}
      {stats && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Card>
            <CardContent className="flex items-center gap-3 pt-4 pb-4">
              <Activity className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-lg font-bold">
                  {(stats.total_webhooks as number) ?? webhooks.length}
                </p>
                <p className="text-xs text-muted-foreground">Jami webhooklar</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 pt-4 pb-4">
              <Activity className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-lg font-bold">
                  {(stats.successful_deliveries as number) ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">Muvaffaqiyatli</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 pt-4 pb-4">
              <Activity className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-lg font-bold">
                  {(stats.failed_deliveries as number) ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">Muvaffaqiyatsiz</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Webhooks table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>URL</TableHead>
              <TableHead>Hodisalar</TableHead>
              <TableHead>Holat</TableHead>
              <TableHead>Yaratilgan</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
              : webhooks.map((w) => (
                <TableRow key={w.id}>
                  <TableCell className="max-w-[300px] truncate font-mono text-sm">
                    {w.url}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {w.events.slice(0, 3).map((e) => (
                        <Badge key={e} variant="outline" className="text-xs">
                          {e}
                        </Badge>
                      ))}
                      {w.events.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{w.events.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={w.is_active ? "default" : "destructive"}>
                      {w.is_active ? "Faol" : "Faol emas"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(w.created_at).toLocaleDateString("uz")}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => testMutation.mutate(w.id)}
                        >
                          <TestTube className="mr-2 h-4 w-4" />
                          Test yuborish
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => setLogsWebhookId(w.id)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          Jurnallar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => setCbWebhook(w)}
                        >
                          <ShieldAlert className="mr-2 h-4 w-4" />
                          Circuit Breaker
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeleteWebhook(w)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          O'chirish
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            {!isLoading && webhooks.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="py-8 text-center text-muted-foreground"
                >
                  Webhooklar topilmadi
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Circuit breaker dialog */}
      <Dialog
        open={cbWebhook !== null}
        onOpenChange={(open) => !open && setCbWebhook(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5" />
              Circuit Breaker
            </DialogTitle>
            <DialogDescription>
              {cbWebhook?.url}
            </DialogDescription>
          </DialogHeader>
          {cbLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : cbState ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`h-3 w-3 rounded-full ${CB_STATE_COLORS[cbState.state] ?? "bg-gray-400"}`}
                  />
                  <div>
                    <p className="font-medium">{CB_STATE_LABELS[cbState.state] ?? cbState.state}</p>
                    <p className="text-sm text-muted-foreground">
                      Xatolar: {cbState.failure_count}
                    </p>
                  </div>
                </div>
                {cbState.state !== "closed" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => resetCbMutation.mutate(cbWebhook!.id)}
                    disabled={resetCbMutation.isPending}
                  >
                    {resetCbMutation.isPending ? (
                      <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                    )}
                    Tiklash
                  </Button>
                )}
              </div>
              {cbState.last_failure_at && (
                <p className="text-sm text-muted-foreground">
                  Oxirgi xato: {new Date(cbState.last_failure_at).toLocaleString("uz")}
                </p>
              )}
            </div>
          ) : (
            <p className="py-4 text-center text-muted-foreground">
              Ma'lumot mavjud emas
            </p>
          )}
        </DialogContent>
      </Dialog>

      {/* Logs dialog */}
      <Dialog
        open={!!logsWebhookId}
        onOpenChange={(open: boolean) => !open && setLogsWebhookId(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Webhook jurnallari</DialogTitle>
            <DialogDescription>So'nggi yetkazish jurnallari</DialogDescription>
          </DialogHeader>
          {logsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : logs.length > 0 ? (
            <div className="max-h-[400px] space-y-2 overflow-y-auto">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {log.event_type}
                      </Badge>
                      <Badge
                        variant={log.success ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {log.success ? "OK" : "Xato"}
                      </Badge>
                      {log.response_status && (
                        <span className="text-xs text-muted-foreground">
                          {log.response_status}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString("uz")}
                      {log.duration_ms != null && ` · ${log.duration_ms}ms`}
                    </p>
                    {log.error_message && (
                      <p className="mt-1 text-xs text-destructive">
                        {log.error_message}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    #{log.attempts}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-4 text-center text-muted-foreground">
              Jurnallar topilmadi
            </p>
          )}
        </DialogContent>
      </Dialog>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi webhook</DialogTitle>
            <DialogDescription>
              Hodisa bildirnomalari uchun endpoint qo'shing
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>URL *</Label>
              <Input
                value={form.url}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setForm({ ...form, url: e.target.value })
                }
                placeholder="https://example.com/webhook"
              />
            </div>
            <div className="space-y-2">
              <Label>Tavsif</Label>
              <Textarea
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                placeholder="Ushbu webhook haqida qisqa tavsif"
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Hodisalar *</Label>
              <div className="flex flex-wrap gap-2">
                {EVENT_OPTIONS.map((event) => (
                  <Badge
                    key={event}
                    variant={form.events.includes(event) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleEvent(event)}
                  >
                    {event}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={() =>
                createMutation.mutate({
                  url: form.url,
                  events: form.events,
                  description: form.description || undefined,
                })
              }
              disabled={
                createMutation.isPending ||
                !form.url ||
                form.events.length === 0
              }
            >
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Yaratish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteWebhook !== null}
        onOpenChange={(open) => !open && setDeleteWebhook(null)}
        title="Webhookni o'chirish"
        description={`"${deleteWebhook?.url}" ni o'chirishni tasdiqlaysizmi?`}
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteWebhook) {
            deleteMutation.mutate(deleteWebhook.id);
            setDeleteWebhook(null);
          }
        }}
      />
    </div>
  );
}
