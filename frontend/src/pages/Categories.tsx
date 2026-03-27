import { useState } from "react";
import { Plus, Pencil, Trash2, Loader2, FolderOpen, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { EmptyState } from "@/components/common/EmptyState";
import {
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from "@/hooks/useCategories";
import { categoriesApi } from "@/services/categoriesApi";
import type { Category, CategoryCreate, CategoryUpdate } from "@/types";

export default function Categories() {
  const [createOpen, setCreateOpen] = useState(false);
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [deleteCategory, setDeleteCategory] = useState<Category | null>(null);
  const [createForm, setCreateForm] = useState<CategoryCreate>({ name: "", description: "" });
  const [editForm, setEditForm] = useState<CategoryUpdate>({});

  const { data, isLoading } = useCategories();
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();

  const categories: Category[] = data?.data?.data ?? [];

  const openEdit = (c: Category) => {
    setEditCategory(c);
    setEditForm({ name: c.name, description: c.description ?? "" });
  };

  const handleCreate = () => {
    if (!createForm.name.trim()) return;
    createMutation.mutate(createForm, {
      onSuccess: () => {
        setCreateOpen(false);
        setCreateForm({ name: "", description: "" });
      },
    });
  };

  const handleUpdate = () => {
    if (!editCategory) return;
    updateMutation.mutate(
      { id: editCategory.id, data: editForm },
      { onSuccess: () => setEditCategory(null) },
    );
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Kategoriyalar"
        description="Sinflar, bo'limlar va guruhlarni boshqarish"
        actions={
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Yangi kategoriya
          </Button>
        }
      />

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nomi</TableHead>
              <TableHead>Tavsif</TableHead>
              <TableHead>A'zolar</TableHead>
              <TableHead className="w-20" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 5 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : categories.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {c.description || "—"}
                    </TableCell>
                    <TableCell>
                      <MemberCount categoryId={c.id} />
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => openEdit(c)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => setDeleteCategory(c)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
            {!isLoading && categories.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>
                  <EmptyState
                    icon={FolderOpen}
                    title="Kategoriyalar topilmadi"
                    description="Sinf yoki guruh yaratish uchun tugmani bosing"
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
            if (!open) setCreateForm({ name: "", description: "" });
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi kategoriya</DialogTitle>
            <DialogDescription>Sinf, bo'lim yoki guruh yarating</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Nomi *</Label>
              <Input
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="masalan: 7-A, O'qituvchilar, IT bo'lim"
              />
            </div>
            <div className="space-y-2">
              <Label>Tavsif</Label>
              <Input
                value={createForm.description ?? ""}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                placeholder="Ixtiyoriy"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending || !createForm.name.trim()}
            >
              {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Yaratish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      <Dialog
        open={editCategory !== null}
        onOpenChange={(open) => !open && setEditCategory(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Kategoriyani tahrirlash</DialogTitle>
            <DialogDescription>{editCategory?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Nomi *</Label>
              <Input
                value={editForm.name ?? ""}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Tavsif</Label>
              <Input
                value={editForm.description ?? ""}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditCategory(null)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={updateMutation.isPending || !editForm.name?.trim()}
            >
              {updateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Saqlash
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteCategory !== null}
        onOpenChange={(open) => !open && setDeleteCategory(null)}
        title={`"${deleteCategory?.name}" kategoriyasini o'chirish`}
        description="Bu kategoriya o'chiriladi. Unga biriktirilgan a'zolarning kategoriya aloqasi uziladi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteCategory) {
            deleteMutation.mutate(deleteCategory.id);
            setDeleteCategory(null);
          }
        }}
      />
    </div>
  );
}

function MemberCount({ categoryId }: { categoryId: number }) {
  const { data } = useQuery({
    queryKey: ["category-stats", categoryId],
    queryFn: () => categoriesApi.stats(categoryId),
    staleTime: 60_000,
  });
  const stats = data?.data?.data;
  if (!stats) return <span className="text-muted-foreground text-sm">—</span>;
  return (
    <span className="flex items-center gap-1 text-sm">
      <Users className="h-3.5 w-3.5 text-muted-foreground" />
      {stats.active} / {stats.total}
    </span>
  );
}
