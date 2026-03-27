import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Users,
  Monitor,
  X,
  Plus,
  RotateCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";

import {
  useAccessGroup,
  useAddGroupCategory,
  useAddGroupStudent,
  useRemoveGroupStudent,
  useSyncGroup,
  useRetryStudentSync,
  useAddGroupDevice,
  useRemoveGroupDevice,
} from "@/hooks/useAccessGroups";
import { useCategories } from "@/hooks/useCategories";
import { useStudents } from "@/hooks/useStudents";
import { useDevices } from "@/hooks/useDevices";
import type { AccessGroupMembership } from "@/types";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Sync status badge
// ---------------------------------------------------------------------------

function SyncBadge({ status }: { status: string }) {
  if (status === "synced")
    return (
      <Badge
        variant="outline"
        className="gap-1 text-green-600 border-green-300 shrink-0"
      >
        <CheckCircle2 className="h-3 w-3" />
        Sinxronlangan
      </Badge>
    );
  if (status === "failed")
    return (
      <Badge
        variant="outline"
        className="gap-1 text-destructive border-destructive/40 shrink-0"
      >
        <XCircle className="h-3 w-3" />
        Muvaffaqiyatsiz
      </Badge>
    );
  return (
    <Badge
      variant="outline"
      className="gap-1 text-yellow-600 border-yellow-300 shrink-0"
    >
      <AlertCircle className="h-3 w-3" />
      Kutilmoqda
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Left panel: add by category or individual student
// ---------------------------------------------------------------------------

function AddPanel({
  groupId,
  memberIds,
  currentDeviceIds,
}: {
  groupId: number;
  memberIds: Set<string>;
  currentDeviceIds: Set<number>;
}) {
  const [studentSearch, setStudentSearch] = useState("");
  const [addingStudentId, setAddingStudentId] = useState<string | null>(null);

  const { data: catData } = useCategories();
  const categories = catData?.data?.data ?? [];

  const { data: studentsData } = useStudents({ per_page: 500 });
  const allStudents = studentsData?.data?.data ?? [];

  const { data: devicesData } = useDevices();
  const allDevices = devicesData?.data?.data ?? [];

  const addCategory = useAddGroupCategory();
  const addStudent = useAddGroupStudent();
  const addDevice = useAddGroupDevice();
  const removeDevice = useRemoveGroupDevice();

  const availableStudents = useMemo(
    () =>
      allStudents.filter(
        (s) =>
          !memberIds.has(s.id) &&
          s.name.toLowerCase().includes(studentSearch.toLowerCase()),
      ),
    [allStudents, memberIds, studentSearch],
  );

  return (
    <div className="rounded-lg border bg-card h-full flex flex-col">
      <div className="px-4 py-3 border-b">
        <h2 className="font-semibold text-sm">A'zolar qo'shish</h2>
      </div>

      <Tabs
        defaultValue="categories"
        className="flex-1 flex flex-col overflow-hidden"
      >
        <div className="px-4 pt-3">
          <TabsList className="w-full">
            <TabsTrigger value="categories" className="flex-1 text-xs">
              Kategoriyalar
            </TabsTrigger>
            <TabsTrigger value="students" className="flex-1 text-xs">
              O'quvchilar
            </TabsTrigger>
            <TabsTrigger value="devices" className="flex-1 text-xs">
              Qurilmalar
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent
          value="categories"
          className="flex-1 overflow-y-auto px-4 pb-4 mt-3 space-y-1"
        >
          {categories.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Kategoriyalar topilmadi
            </p>
          ) : (
            (() => {
              const roots = categories.filter((c) => c.parent_id === null);
              const childrenOf = (parentId: number) =>
                categories.filter((c) => c.parent_id === parentId);

              const renderRow = (cat: (typeof categories)[0], depth: number) => {
                const subs = childrenOf(cat.id);
                return (
                  <div key={cat.id}>
                    <div
                      className={cn(
                        "flex items-center justify-between rounded-md border px-3 py-2.5",
                        depth > 0 && "ml-4 border-l-2 border-l-muted rounded-l-none",
                      )}
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium">{cat.name}</p>
                        {cat.description && (
                          <p className="text-xs text-muted-foreground truncate">
                            {cat.description}
                          </p>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 shrink-0 ml-2"
                        disabled={addCategory.isPending}
                        onClick={() =>
                          addCategory.mutate({ groupId, categoryId: cat.id })
                        }
                      >
                        {addCategory.isPending ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Plus className="h-3.5 w-3.5" />
                        )}
                        <span className="ml-1">Qo'shish</span>
                      </Button>
                    </div>
                    {subs.length > 0 && (
                      <div className="ml-3 mt-1 space-y-1">
                        {subs.map((sub) => renderRow(sub, depth + 1))}
                      </div>
                    )}
                  </div>
                );
              };

              return roots.map((root) => renderRow(root, 0));
            })()
          )}
        </TabsContent>

        <TabsContent
          value="students"
          className="flex-1 flex flex-col overflow-hidden px-4 pb-4 mt-3"
        >
          <Input
            placeholder="Ism bo'yicha qidirish..."
            value={studentSearch}
            onChange={(e) => {
              setStudentSearch(e.target.value);
              setAddingStudentId(null);
            }}
            className="mb-3"
          />
          <div className="flex-1 overflow-y-auto space-y-1 rounded-md border divide-y">
            {availableStudents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">
                {studentSearch
                  ? "Natija yo'q"
                  : "Barcha o'quvchilar qo'shilgan"}
              </p>
            ) : (
              availableStudents.slice(0, 50).map((s) => (
                <button
                  key={s.id}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-muted transition-colors",
                    addingStudentId === s.id && "bg-primary/10",
                  )}
                  onClick={() => {
                    setAddingStudentId(s.id);
                    addStudent.mutate(
                      { groupId, studentId: s.id },
                      { onSuccess: () => setAddingStudentId(null) },
                    );
                  }}
                >
                  <div className="text-left">
                    <span className="font-medium">{s.name}</span>
                    {s.class_name && (
                      <span className="text-muted-foreground ml-2 text-xs">
                        {s.class_name}
                      </span>
                    )}
                  </div>
                  {addingStudentId === s.id && addStudent.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                  ) : (
                    <Plus className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                </button>
              ))
            )}
          </div>
        </TabsContent>

        {/* Devices tab */}
        <TabsContent
          value="devices"
          className="flex-1 overflow-y-auto px-4 pb-4 mt-3 space-y-2"
        >
          {allDevices.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Qurilmalar sozlanmagan
            </p>
          ) : (
            allDevices.map((device) => {
              const isAdded = currentDeviceIds.has(device.id);
              return (
                <div
                  key={device.id}
                  className={cn(
                    "flex items-center justify-between rounded-md border px-3 py-2.5",
                    isAdded && "border-primary/30 bg-primary/5",
                  )}
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{device.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {device.ip_address}
                    </p>
                  </div>
                  {isAdded ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 shrink-0 ml-2 text-destructive border-destructive/30 hover:bg-destructive/10 hover:text-destructive"
                      disabled={removeDevice.isPending}
                      onClick={() =>
                        removeDevice.mutate({ groupId, deviceId: device.id })
                      }
                    >
                      {removeDevice.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <X className="h-3.5 w-3.5" />
                      )}
                      <span className="ml-1">O'chirish</span>
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 shrink-0 ml-2"
                      disabled={addDevice.isPending}
                      onClick={() =>
                        addDevice.mutate({ groupId, deviceId: device.id })
                      }
                    >
                      {addDevice.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Plus className="h-3.5 w-3.5" />
                      )}
                      <span className="ml-1">Qo'shish</span>
                    </Button>
                  )}
                </div>
              );
            })
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Right panel: members with sync status
// ---------------------------------------------------------------------------

type SyncFilter = "all" | "synced" | "pending" | "failed";

function MembersPanel({
  groupId,
  members,
}: {
  groupId: number;
  members: AccessGroupMembership[];
}) {
  const [filter, setFilter] = useState<SyncFilter>("all");
  const syncGroup = useSyncGroup();
  const removeStudent = useRemoveGroupStudent();
  const retrySync = useRetryStudentSync();

  const counts = useMemo(
    () => ({
      all: members.length,
      synced: members.filter((m) => m.sync_status === "synced").length,
      pending: members.filter((m) => m.sync_status === "pending").length,
      failed: members.filter((m) => m.sync_status === "failed").length,
    }),
    [members],
  );

  const visible = useMemo(
    () =>
      filter === "all"
        ? members
        : members.filter((m) => m.sync_status === filter),
    [members, filter],
  );

  const FILTERS: { key: SyncFilter; label: string; color?: string }[] = [
    { key: "all", label: `Barchasi ${counts.all}` },
    {
      key: "synced",
      label: `Sinxronlangan ${counts.synced}`,
      color: "text-green-600",
    },
    {
      key: "pending",
      label: `Kutilmoqda ${counts.pending}`,
      color: "text-yellow-600",
    },
    {
      key: "failed",
      label: `Muvaffaqiyatsiz ${counts.failed}`,
      color: "text-destructive",
    },
  ];

  return (
    <div className="rounded-lg border bg-card h-full flex flex-col">
      <div className="px-4 py-3 border-b flex items-center justify-between">
        <h2 className="font-semibold text-sm">A'zolar holati</h2>
        <Button
          size="sm"
          variant="outline"
          className="h-7"
          disabled={syncGroup.isPending || members.length === 0}
          onClick={() => syncGroup.mutate(groupId)}
        >
          {syncGroup.isPending ? (
            <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          )}
          Hammasini sinxronlash
        </Button>
      </div>

      <div className="px-4 py-2 border-b flex gap-4 text-xs">
        <span className="text-muted-foreground">
          Jami: <b className="text-foreground">{counts.all}</b>
        </span>
        <span className="text-green-600">
          Sinxronlangan: <b>{counts.synced}</b>
        </span>
        <span className="text-yellow-600">
          Kutilmoqda: <b>{counts.pending}</b>
        </span>
        <span className="text-destructive">
          Muvaffaqiyatsiz: <b>{counts.failed}</b>
        </span>
      </div>

      <div className="px-4 pt-2 pb-1 flex gap-1 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              "px-2.5 py-1 rounded-md text-xs font-medium transition-colors",
              filter === f.key
                ? "bg-primary text-primary-foreground"
                : cn("hover:bg-muted", f.color ?? "text-muted-foreground"),
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      <Separator />

      <div className="flex-1 overflow-y-auto divide-y">
        {members.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-10 w-10 text-muted-foreground/40 mb-3" />
            <p className="text-sm text-muted-foreground">
              Hali o'quvchilar qo'shilmagan
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Chap paneldan kategoriya yoki alohida o'quvchi qo'shing
            </p>
          </div>
        ) : visible.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            Bu holat bilan a'zolar yo'q
          </p>
        ) : (
          visible.map((m) => (
            <div
              key={m.id}
              className="flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors"
            >
              <div
                className={cn(
                  "h-2 w-2 rounded-full shrink-0",
                  m.sync_status === "synced" && "bg-green-500",
                  m.sync_status === "pending" && "bg-yellow-400",
                  m.sync_status === "failed" && "bg-destructive",
                )}
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium truncate">
                    {m.student.name}
                  </p>
                  {m.student.class_name && (
                    <span className="text-xs text-muted-foreground shrink-0">
                      {m.student.class_name}
                    </span>
                  )}
                </div>
                {m.sync_error && (
                  <p className="text-xs text-destructive mt-0.5 truncate">
                    {m.sync_error}
                  </p>
                )}
                {m.synced_at && m.sync_status === "synced" && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {new Date(m.synced_at).toLocaleString("uz")}
                  </p>
                )}
              </div>

              <SyncBadge status={m.sync_status} />

              {/* Individual retry button (shown for failed status) */}
              {m.sync_status === "failed" && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-muted-foreground hover:text-primary shrink-0"
                  title="Sinxronlashni qayta urinish"
                  onClick={() =>
                    retrySync.mutate({
                      groupId,
                      studentId: m.student_id,
                    })
                  }
                  disabled={retrySync.isPending}
                >
                  {retrySync.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <RotateCcw className="h-3.5 w-3.5" />
                  )}
                </Button>
              )}

              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive shrink-0"
                onClick={() =>
                  removeStudent.mutate({
                    groupId,
                    studentId: m.student_id,
                  })
                }
                disabled={removeStudent.isPending}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AccessGroupDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const groupId = Number(id);

  const { data, isLoading } = useAccessGroup(groupId);
  const group = data?.data?.data ?? null;

  const memberIds = useMemo(
    () => new Set(group?.students.map((m) => m.student_id) ?? []),
    [group],
  );

  const deviceIds = useMemo(
    () => new Set(group?.devices.map((d) => d.id) ?? []),
    [group],
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-6 w-48" />
        <div className="grid grid-cols-2 gap-4 mt-6">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="text-center py-16">
        <p className="text-muted-foreground">Kirish guruhi topilmadi</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/access-groups")}
        >
          Orqaga
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="mt-0.5 h-8 w-8 p-0 shrink-0"
            onClick={() => navigate("/access-groups")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold tracking-tight">{group.name}</h1>
              {!group.is_active && (
                <Badge variant="secondary">Faol emas</Badge>
              )}
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground flex-wrap">
              {group.timetable && (
                <span className="font-medium text-foreground">
                  {group.timetable.name}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <Monitor className="h-3.5 w-3.5" />
                {group.devices.length} ta qurilma
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5" />
                {group.students.length} ta a'zo
              </span>
            </div>
            {group.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {group.description}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Two-panel layout */}
      <div
        className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4 flex-1 min-h-0"
        style={{ minHeight: "520px" }}
      >
        <AddPanel groupId={groupId} memberIds={memberIds} currentDeviceIds={deviceIds} />
        <MembersPanel groupId={groupId} members={group.students} />
      </div>
    </div>
  );
}
