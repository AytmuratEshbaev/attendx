import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import {
  Plus,
  Trash2,
  RefreshCw,
  Loader2,
  Wifi,
  WifiOff,
  Pencil,
  Server,
  CheckSquare,
  Square,
  X,
  ArrowUpDown,
  Camera,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { devicesApi } from "@/services/devicesApi";
import {
  useDevices,
  useCreateDevice,
  useUpdateDevice,
  useDeleteDevice,
  useSyncDevice,
} from "@/hooks/useDevices";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import type { Device, DeviceCreate } from "@/types";
import { cn } from "@/lib/utils";
import { useSelection } from "@/hooks/useSelection";

// ─── Device Snapshot (kamera ko'rinishi) ────────────────────────────────────
function DeviceSnapshot({ device }: { device: Device }) {
  const [src, setSrc] = useState<string>("");
  const [error, setError] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSnapshot = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/devices/${device.id}/snapshot`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) { setError(true); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setSrc((prev) => { if (prev) URL.revokeObjectURL(prev); return url; });
      setError(false);
    } catch {
      setError(true);
    }
  }, [device.id, accessToken]);

  useEffect(() => {
    if (!device.is_active) return;
    fetchSnapshot();
    intervalRef.current = setInterval(fetchSnapshot, 4000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [device.is_active, fetchSnapshot]);

  if (!device.is_active) return null;

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-md bg-black">
      {error ? (
        <div className="flex h-full flex-col items-center justify-center gap-1.5 text-muted-foreground">
          <Camera className="h-8 w-8 opacity-25" />
          <span className="text-xs">Signal yo'q</span>
        </div>
      ) : src ? (
        <img src={src} alt={device.name} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full items-center justify-center">
          <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  );
}

function isDeviceOnline(device: Device): boolean {
  if (!device.is_active) return false;
  if (!device.last_online_at) return false;
  const diff = Date.now() - new Date(device.last_online_at).getTime();
  return diff < 2 * 60 * 1000;
}

const EMPTY_FORM: DeviceCreate = {
  name: "",
  ip_address: "",
  username: "admin",
  password: "",
  port: 80,
  is_entry: true,
};

export default function Devices() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editDevice, setEditDevice] = useState<Device | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState<DeviceCreate>({ ...EMPTY_FORM });

  // Filter & sort
  const [filterType, setFilterType] = useState<"all" | "entry" | "exit">("all");
  const [sortBy, setSortBy] = useState<"name" | "ip" | "status" | "last_seen">("name");

  // Selection mode
  const [selecting, setSelecting] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [bulkSyncing, setBulkSyncing] = useState(false);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);

  const { data, isLoading } = useDevices();
  const createMutation = useCreateDevice();
  const updateMutation = useUpdateDevice();
  const deleteMutation = useDeleteDevice();
  const syncMutation = useSyncDevice();

  const devices = data?.data?.data ?? [];
  const onlineCount = devices.filter(isDeviceOnline).length;

  const visibleDevices = useMemo(() => {
    let list = [...devices];

    // Filter
    if (filterType === "entry") list = list.filter((d) => d.is_entry);
    else if (filterType === "exit") list = list.filter((d) => !d.is_entry);

    // Sort
    list.sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      if (sortBy === "ip") return a.ip_address.localeCompare(b.ip_address);
      if (sortBy === "status") {
        return Number(isDeviceOnline(b)) - Number(isDeviceOnline(a));
      }
      if (sortBy === "last_seen") {
        const ta = a.last_online_at ? new Date(a.last_online_at).getTime() : 0;
        const tb = b.last_online_at ? new Date(b.last_online_at).getTime() : 0;
        return tb - ta;
      }
      return 0;
    });

    return list;
  }, [devices, filterType, sortBy]);

  const {
    selectedIds: selected,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
  } = useSelection<Device>(devices, (d) => d.id);

  const exitSelecting = () => {
    setSelecting(false);
    clearSelection();
  };

  // --- Bulk actions ---
  const handleBulkSync = async () => {
    setBulkSyncing(true);
    const ids = Array.from(selected) as number[];
    const results = await Promise.allSettled(ids.map((id) => devicesApi.sync(id)));
    const failed = results.filter((r) => r.status === "rejected").length;
    setBulkSyncing(false);
    if (failed === 0) toast.success(`${ids.length} ta qurilma sinxronlanmoqda`);
    else toast.warning(`${ids.length - failed} ta muvaffaqiyatli, ${failed} ta muvaffaqiyatsiz`);
  };

  const handleBulkDelete = async () => {
    setBulkDeleting(true);
    const ids = Array.from(selected) as number[];
    const results = await Promise.allSettled(ids.map((id) => devicesApi.delete(id)));
    const failed = results.filter((r) => r.status === "rejected").length;
    setBulkDeleting(false);
    setConfirmBulkDelete(false);
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    if (failed === 0) {
      toast.success(`${ids.length} ta qurilma o'chirildi`);
      exitSelecting();
    } else {
      toast.warning(`${ids.length - failed} ta o'chirildi, ${failed} ta muvaffaqiyatsiz`);
      clearSelection();
    }
  };

  // --- Single device actions ---
  const openEdit = (d: Device) => {
    setEditDevice(d);
    setForm({
      name: d.name,
      ip_address: d.ip_address,
      port: d.port,
      username: d.username ?? "admin",
      password: "",
      is_entry: d.is_entry,
    });
  };

  const handleCreate = () => {
    createMutation.mutate(form, {
      onSuccess: () => {
        setCreateOpen(false);
        setForm({ ...EMPTY_FORM });
      },
    });
  };

  const handleUpdate = () => {
    if (!editDevice) return;
    const data: Partial<DeviceCreate> = {
      name: form.name,
      ip_address: form.ip_address,
      port: form.port,
      username: form.username,
      is_entry: form.is_entry,
    };
    if (form.password) data.password = form.password;
    updateMutation.mutate(
      { id: editDevice.id, data },
      {
        onSuccess: () => {
          setEditDevice(null);
          setForm({ ...EMPTY_FORM });
        },
      },
    );
  };

  const allSelected = devices.length > 0 && selected.size === devices.length;
  const someSelected = selected.size > 0 && !allSelected;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Qurilmalar"
        description={`${devices.length} ta qurilma · ${onlineCount} ta onlayn`}
        actions={
          <div className="flex gap-2">
            {!selecting ? (
              <>
                {devices.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelecting(true)}
                  >
                    <CheckSquare className="mr-2 h-4 w-4" />
                    Tanlash
                  </Button>
                )}
                <Button size="sm" onClick={() => setCreateOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Yangi qurilma
                </Button>
              </>
            ) : (
              <Button variant="outline" size="sm" onClick={exitSelecting}>
                <X className="mr-2 h-4 w-4" />
                Bekor qilish
              </Button>
            )}
          </div>
        }
      />

      {/* Filter & Sort bar */}
      {!selecting && devices.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          {/* Filter buttons */}
          <div className="flex rounded-md border">
            {(["all", "entry", "exit"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={cn(
                  "px-3 py-1.5 text-sm font-medium transition-colors first:rounded-l-md last:rounded-r-md",
                  filterType === type
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {type === "all" ? "Barchasi" : type === "entry" ? "Kirish" : "Chiqish"}
              </button>
            ))}
          </div>

          {/* Sort select */}
          <div className="flex items-center gap-2 ml-auto">
            <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
            <Select value={sortBy} onValueChange={(v) => setSortBy(v as typeof sortBy)}>
              <SelectTrigger className="h-9 w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Nomi bo'yicha</SelectItem>
                <SelectItem value="ip">IP bo'yicha</SelectItem>
                <SelectItem value="status">Holati bo'yicha</SelectItem>
                <SelectItem value="last_seen">Oxirgi onlayn</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Bulk action toolbar */}
      {selecting && (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/40 px-4 py-2.5">
          <button
            className="flex items-center gap-2 text-sm font-medium"
            onClick={toggleSelectAll}
          >
            {allSelected ? (
              <CheckSquare className="h-4 w-4 text-primary" />
            ) : someSelected ? (
              <Square className="h-4 w-4 text-primary opacity-60" />
            ) : (
              <Square className="h-4 w-4 text-muted-foreground" />
            )}
            {allSelected ? "Hammasini bekor qilish" : "Hammasini tanlash"}
          </button>

          <span className="text-sm text-muted-foreground">
            {selected.size > 0 ? `${selected.size} ta tanlandi` : "Hech narsa tanlanmagan"}
          </span>

          <div className="ml-auto flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={selected.size === 0 || bulkSyncing}
              onClick={handleBulkSync}
            >
              {bulkSyncing ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-3.5 w-3.5" />
              )}
              Sinxronlash
            </Button>
            <Button
              size="sm"
              variant="destructive"
              disabled={selected.size === 0 || bulkDeleting}
              onClick={() => setConfirmBulkDelete(true)}
            >
              {bulkDeleting ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="mr-2 h-3.5 w-3.5" />
              )}
              O'chirish
            </Button>
          </div>
        </div>
      )}

      {/* Device cards grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="glass-card border-none premium-shadow">
              <CardContent className="pt-6">
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : devices.length === 0 ? (
        <EmptyState
          icon={Server}
          title="Qurilmalar topilmadi"
          description="Hikvision qurilma qo'shish uchun tugmani bosing"
          action={
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Yangi qurilma
            </Button>
          }
        />
      ) : visibleDevices.length === 0 ? (
        <EmptyState
          icon={Server}
          title="Natija yo'q"
          description="Tanlangan filtrga mos qurilmalar topilmadi"
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visibleDevices.map((d) => {
            const online = isDeviceOnline(d);
            const isSelected = selected.has(d.id);
            return (
              <Card
                key={d.id}
                className={cn(
                  "glass-card border-none premium-shadow transition-all duration-300 relative overflow-hidden group",
                  selecting && "cursor-pointer hover:border-primary/50",
                  isSelected && "border-primary bg-primary/5 ring-1 ring-primary",
                )}
                onClick={selecting ? () => toggleSelect(d.id) : undefined}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity -z-10" />
                <CardHeader className="flex flex-row items-start justify-between pb-4 bg-white/30 dark:bg-slate-900/30 rounded-t-xl backdrop-blur-md border-b border-border/50 mb-4">
                  <div className="flex items-center gap-2">
                    {selecting ? (
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSelect(d.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="mt-0.5"
                      />
                    ) : (
                      <span
                        className={cn(
                          "mt-1 h-2.5 w-2.5 rounded-full",
                          online ? "bg-green-500" : "bg-red-400",
                        )}
                      />
                    )}
                    <div>
                      <CardTitle className="text-base">{d.name}</CardTitle>
                      <p className="text-xs text-muted-foreground font-mono">
                        {d.ip_address}:{d.port}
                      </p>
                    </div>
                  </div>
                  <Badge variant={online ? "default" : "destructive"} className="gap-1 shadow-sm mt-1">
                    {online ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                    {online ? "Onlayn" : "Oflayn"}
                  </Badge>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-2 text-sm">
                    <Badge variant="outline">
                      {d.is_entry ? "Kirish" : "Chiqish"}
                    </Badge>
                    {d.model && (
                      <Badge variant="outline" className="text-xs">
                        {d.model}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Oxirgi ulanish:{" "}
                    {d.last_online_at
                      ? new Date(d.last_online_at).toLocaleString("uz")
                      : "Hech qachon"}
                  </p>
                  <DeviceSnapshot device={d} />
                  {!selecting && (
                    <div className="flex gap-2 border-t pt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => syncMutation.mutate(d.id)}
                        disabled={syncMutation.isPending}
                      >
                        <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", syncMutation.isPending && "animate-spin")} />
                        Sinxronlash
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEdit(d)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setDeleteId(d.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create dialog */}
      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open);
          if (!open) setForm({ ...EMPTY_FORM });
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi qurilma</DialogTitle>
            <DialogDescription>
              Hikvision qurilma ma'lumotlarini kiriting
            </DialogDescription>
          </DialogHeader>
          <DeviceForm form={form} setForm={setForm} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending || !form.name || !form.ip_address || !form.password}
            >
              {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Qo'shish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      <Dialog
        open={editDevice !== null}
        onOpenChange={(open) => {
          if (!open) {
            setEditDevice(null);
            setForm({ ...EMPTY_FORM });
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Qurilmani tahrirlash</DialogTitle>
            <DialogDescription>
              Qurilma ma'lumotlarini yangilang
            </DialogDescription>
          </DialogHeader>
          <DeviceForm form={form} setForm={setForm} isEdit />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDevice(null)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateMutation.isPending || !form.name || !form.ip_address}
            >
              {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Saqlash
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Single delete confirmation */}
      <ConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="Qurilmani o'chirish"
        description="Bu amalni bekor qilib bo'lmaydi. Qurilma butunlay o'chiriladi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteId !== null) {
            deleteMutation.mutate(deleteId);
            setDeleteId(null);
          }
        }}
      />

      {/* Bulk delete confirmation */}
      <ConfirmDialog
        open={confirmBulkDelete}
        onOpenChange={(open) => !open && setConfirmBulkDelete(false)}
        title={`${selected.size} ta qurilmani o'chirish`}
        description="Tanlangan qurilmalar butunlay o'chiriladi. Bu amalni bekor qilib bo'lmaydi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={handleBulkDelete}
      />
    </div>
  );
}

function DeviceForm({
  form,
  setForm,
  isEdit,
}: {
  form: DeviceCreate;
  setForm: (f: DeviceCreate) => void;
  isEdit?: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Nomi *</Label>
        <Input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          placeholder="Asosiy kirish"
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>IP manzil *</Label>
          <Input
            value={form.ip_address}
            onChange={(e) => setForm({ ...form, ip_address: e.target.value })}
            placeholder="192.168.1.100"
          />
        </div>
        <div className="space-y-2">
          <Label>Port</Label>
          <Input
            type="number"
            value={form.port ?? 80}
            onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) || 80 })}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label>Foydalanuvchi nomi *</Label>
        <Input
          value={form.username ?? "admin"}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          placeholder="admin"
        />
      </div>
      <div className="space-y-2">
        <Label>{isEdit ? "Parol (o'zgartirmaslik uchun bo'sh qoldiring)" : "Parol *"}</Label>
        <Input
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
      </div>
      <div className="flex items-center gap-2">
        <Switch
          checked={form.is_entry ?? true}
          onCheckedChange={(v) => setForm({ ...form, is_entry: v })}
        />
        <Label>Kirish qurilmasi</Label>
      </div>
    </div>
  );
}
