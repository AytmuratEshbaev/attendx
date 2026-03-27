import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Plus,
  MoreHorizontal,
  Loader2,
  ShieldCheck,
  UserCog,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { usersApi } from "@/services/usersApi";
import { getErrorMessage } from "@/services/api";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import type { User, UserCreate, UserUpdate } from "@/types";

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  teacher: "O'qituvchi",
};

export default function Users() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [deleteUser, setDeleteUser] = useState<User | null>(null);
  const [createForm, setCreateForm] = useState<UserCreate>({
    username: "",
    email: "",
    password: "",
    role: "teacher",
  });
  const [editForm, setEditForm] = useState<UserUpdate>({});

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => usersApi.create(data),
    onSuccess: () => {
      toast.success("Foydalanuvchi yaratildi");
      setCreateOpen(false);
      setCreateForm({ username: "", email: "", password: "", role: "teacher" });
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) =>
      usersApi.update(id, data),
    onSuccess: () => {
      toast.success("Foydalanuvchi yangilandi");
      setEditUser(null);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => usersApi.delete(id),
    onSuccess: () => {
      toast.success("Foydalanuvchi o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const users: User[] = data?.data?.data ?? [];

  const openEditDialog = (u: User) => {
    setEditUser(u);
    setEditForm({
      role: u.role,
      is_active: u.is_active,
    });
  };

  const handleToggleActive = (u: User) => {
    updateMutation.mutate({
      id: u.id,
      data: { is_active: !u.is_active },
    });
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Foydalanuvchilar"
        description="Tizim foydalanuvchilarini boshqarish"
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Yangi foydalanuvchi
          </Button>
        }
      />

      {/* Users table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Foydalanuvchi nomi</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Holat</TableHead>
              <TableHead>So'nggi kirish</TableHead>
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {u.role === "super_admin" && (
                          <ShieldCheck className="h-4 w-4 text-primary" />
                        )}
                        {u.username}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {u.email || "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {ROLE_LABELS[u.role] ?? u.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={u.is_active ? "active" : "inactive"} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {u.last_login_at
                        ? new Date(u.last_login_at).toLocaleString("uz")
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEditDialog(u)}>
                            <UserCog className="mr-2 h-4 w-4" />
                            Tahrirlash
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleToggleActive(u)}>
                            {u.is_active ? "O'chirish" : "Faollashtirish"}
                          </DropdownMenuItem>
                          {u.role !== "super_admin" && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => setDeleteUser(u)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                O'chirish
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
            {!isLoading && users.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  <EmptyState
                    icon={ShieldCheck}
                    title="Foydalanuvchilar topilmadi"
                  />
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create dialog */}
      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          if (!createMutation.isPending) {
            setCreateOpen(open);
            if (!open) setCreateForm({ username: "", email: "", password: "", role: "teacher" });
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi foydalanuvchi</DialogTitle>
            <DialogDescription>
              Tizim foydalanuvchisi yaratish
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Foydalanuvchi nomi *</Label>
              <Input
                value={createForm.username}
                onChange={(e) =>
                  setCreateForm({ ...createForm, username: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={createForm.email ?? ""}
                onChange={(e) =>
                  setCreateForm({ ...createForm, email: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Parol *</Label>
              <Input
                type="password"
                value={createForm.password}
                onChange={(e) =>
                  setCreateForm({ ...createForm, password: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Rol *</Label>
              <Select
                value={createForm.role}
                onValueChange={(v: "super_admin" | "admin" | "teacher") =>
                  setCreateForm({ ...createForm, role: v })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="teacher">O'qituvchi</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="super_admin">Super Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => createMutation.mutate(createForm)}
              disabled={
                createMutation.isPending ||
                !createForm.username ||
                (createForm.password?.length ?? 0) < 6
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

      {/* Edit dialog */}
      <Dialog
        open={editUser !== null}
        onOpenChange={(open) => !open && setEditUser(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Foydalanuvchini tahrirlash</DialogTitle>
            <DialogDescription>
              {editUser?.username} — rol va holatni o'zgartirish
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Rol</Label>
              <Select
                value={editForm.role}
                onValueChange={(v: "super_admin" | "admin" | "teacher") =>
                  setEditForm({ ...editForm, role: v })
                }
                disabled={editUser?.role === "super_admin"}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="teacher">O'qituvchi</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="super_admin">Super Admin</SelectItem>
                </SelectContent>
              </Select>
              {editUser?.role === "super_admin" && (
                <p className="text-xs text-muted-foreground">
                  Super admin rolini o'zgartirib bo'lmaydi
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditUser(null)}>
              Bekor qilish
            </Button>
            <Button
              onClick={() => {
                if (editUser) {
                  updateMutation.mutate({ id: editUser.id, data: editForm });
                }
              }}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Saqlash
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteUser !== null}
        onOpenChange={(open) => !open && setDeleteUser(null)}
        title="Foydalanuvchini o'chirish"
        description={`"${deleteUser?.username}" ni o'chirishni tasdiqlaysizmi? Bu amalni bekor qilib bo'lmaydi.`}
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteUser) {
            deleteMutation.mutate(deleteUser.id);
            setDeleteUser(null);
          }
        }}
      />
    </div>
  );
}
