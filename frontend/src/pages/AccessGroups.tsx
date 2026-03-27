import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Trash2,
  Shield,
  Monitor,
  Users,
  ChevronRight,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import {
  useAccessGroups,
  useCreateAccessGroup,
  useDeleteAccessGroup,
} from "@/hooks/useAccessGroups";
import { useTimetables } from "@/hooks/useTimetables";
import type { AccessGroup, AccessGroupCreate } from "@/types";

// ---------------------------------------------------------------------------
// AccessGroup card
// ---------------------------------------------------------------------------

function AccessGroupCard({
  group,
  onClick,
  onDelete,
}: {
  group: AccessGroup;
  onClick: () => void;
  onDelete: () => void;
}) {
  return (
    <Card
      className="cursor-pointer hover:border-primary/50 transition-colors"
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <div className="space-y-1">
          <CardTitle className="text-base flex items-center gap-2">
            {group.name}
            {!group.is_active && (
              <Badge variant="secondary" className="text-xs">
                Faol emas
              </Badge>
            )}
          </CardTitle>
          {group.timetable && (
            <Badge variant="outline" className="text-xs">
              {group.timetable.name}
            </Badge>
          )}
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground mt-1 flex-shrink-0" />
      </CardHeader>
      <CardContent className="space-y-3">
        {group.description && (
          <p className="text-sm text-muted-foreground">{group.description}</p>
        )}
        <div className="flex gap-4 text-sm pt-1">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <Monitor className="h-3.5 w-3.5" />
            {group.devices.length} ta qurilma
          </span>
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <Users className="h-3.5 w-3.5" />
            {group.students.length} ta o'quvchi
          </span>
        </div>
        <div
          className="flex justify-end border-t pt-2"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive hover:bg-destructive/10"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Create dialog
// ---------------------------------------------------------------------------

function CreateGroupDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [form, setForm] = useState<AccessGroupCreate>({
    name: "",
    description: "",
    timetable_id: null,
    is_active: true,
  });

  const createGroup = useCreateAccessGroup();
  const { data: ttData } = useTimetables();
  const timetables = ttData?.data?.data ?? [];

  const handleClose = () => {
    setForm({ name: "", description: "", timetable_id: null, is_active: true });
    onClose();
  };

  const handleSubmit = () => {
    createGroup.mutate(
      {
        ...form,
        description: form.description || undefined,
      },
      { onSuccess: handleClose },
    );
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Yangi kirish guruhi</DialogTitle>
          <DialogDescription>
            Qurilma va o'quvchi kirish huquqlarini boshqarish uchun guruh yarating
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Nomi *</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="1-sinf kirish guruhi"
            />
          </div>

          <div className="space-y-2">
            <Label>Tavsif</Label>
            <Input
              value={form.description ?? ""}
              onChange={(e) =>
                setForm((p) => ({ ...p, description: e.target.value }))
              }
              placeholder="Ixtiyoriy"
            />
          </div>

          <div className="space-y-2">
            <Label>Dars jadvali</Label>
            <Select
              value={form.timetable_id?.toString() ?? "none"}
              onValueChange={(v) =>
                setForm((p) => ({
                  ...p,
                  timetable_id: v === "none" ? null : Number(v),
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Dars jadvali tanlang (ixtiyoriy)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Dars jadvalisiz</SelectItem>
                {timetables.map((tt) => (
                  <SelectItem key={tt.id} value={tt.id.toString()}>
                    {tt.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Bekor qilish
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={createGroup.isPending || !form.name}
          >
            {createGroup.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Yaratish
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AccessGroups() {
  const navigate = useNavigate();
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data, isLoading } = useAccessGroups();
  const deleteGroup = useDeleteAccessGroup();

  const groups: AccessGroup[] = data?.data?.data ?? [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Kirish guruhlari"
        description={`${groups.length} ta guruh`}
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Yangi guruh
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-28 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : groups.length === 0 ? (
        <EmptyState
          icon={Shield}
          title="Kirish guruhlari topilmadi"
          description="Qurilma va o'quvchi kirishini boshqarish uchun guruh yarating"
          action={
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Yangi guruh
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((g) => (
            <AccessGroupCard
              key={g.id}
              group={g}
              onClick={() => navigate(`/access-groups/${g.id}`)}
              onDelete={() => setDeleteId(g.id)}
            />
          ))}
        </div>
      )}

      <CreateGroupDialog open={createOpen} onClose={() => setCreateOpen(false)} />

      <ConfirmDialog
        open={deleteId !== null}
        onOpenChange={(open) => !open && setDeleteId(null)}
        title="Kirish guruhini o'chirish"
        description="Bu amalni bekor qilib bo'lmaydi. Guruh va uning barcha a'zolari butunlay o'chiriladi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteId !== null) {
            deleteGroup.mutate(deleteId, {
              onSuccess: () => setDeleteId(null),
            });
          }
        }}
      />
    </div>
  );
}
