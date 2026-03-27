import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Plus,
  Search,
  Download,
  Upload,
  MoreHorizontal,
  Pencil,
  Trash2,
  ScanFace,
  Loader2,
  List,
  LayoutGrid,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

import { studentsApi } from "@/services/studentsApi";
import { getErrorMessage } from "@/services/api";
import type { StudentCreate, StudentImportResult } from "@/types";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { useDebounce } from "@/hooks/useDebounce";
import { useCategories } from "@/hooks/useCategories";
import { StudentCard } from "@/components/students/StudentCard";
import { useSelection } from "@/hooks/useSelection";

export default function Students() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "super_admin" || user?.role === "admin";
  const { studentsView, setStudentsView } = useUIStore();

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 300);
  const [classFilter, setClassFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<number | null>(null);

  const { data: categoriesData } = useCategories();
  const [createOpen, setCreateOpen] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<StudentCreate>({
    name: "",
    class_name: "",
    employee_no: "",
  });

  // Delete confirmation
  const [deleteId, setDeleteId] = useState<string | null>(null);

  // Bulk selection
  // Replaced with useSelection hook below

  // Import
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importProgress, setImportProgress] = useState(0);
  const [importResult, setImportResult] = useState<StudentImportResult | null>(
    null,
  );
  const [importLoading, setImportLoading] = useState(false);

  // Reset selection when page/search/filter changes
  useEffect(() => {
    // Selection gets cleared when dependencies change but we will handle it with useSelection hook directly
  }, [page, search, classFilter, categoryFilter]);

  const categories = categoriesData?.data?.data ?? [];

  const { data, isLoading } = useQuery({
    queryKey: ["students", page, search, classFilter, categoryFilter],
    queryFn: () =>
      studentsApi.list({
        page,
        per_page: 20,
        search: search || undefined,
        class_name: !categoryFilter && classFilter ? classFilter : undefined,
        category_id: categoryFilter ?? undefined,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.create(data),
    onSuccess: () => {
      toast.success("O'quvchi yaratildi");
      setCreateOpen(false);
      setFormData({ name: "", class_name: "", employee_no: "" });
      setFormErrors({});
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleCreateSubmit = () => {
    const errors: Record<string, string> = {};
    if (!formData.name.trim()) errors.name = "Ismi kiritilishi shart";
    if (!formData.employee_no?.trim()) errors.employee_no = "Xodim raqami kiritilishi shart";
    if (!formData.category_id && !formData.class_name?.trim())
      errors.class_name = "Kategoriya yoki sinf nomi kiritilishi shart";
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    setFormErrors({});
    createMutation.mutate(formData);
  };

  const deleteMutation = useMutation({
    mutationFn: (id: string) => studentsApi.delete(id),
    onSuccess: () => {
      toast.success("O'quvchi o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: string[]) =>
      Promise.all(ids.map((id) => studentsApi.delete(id))),
    onSuccess: () => {
      toast.success(`${selectedIds.size} ta o'quvchi o'chirildi`);
      clearSelection();
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleExport = async (format: string) => {
    try {
      const res = await studentsApi.export({
        format,
        class_name: classFilter || undefined,
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `students.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleImport = async () => {
    if (!importFile) return;
    setImportLoading(true);
    setImportProgress(0);
    setImportResult(null);

    const progressInterval = setInterval(() => {
      setImportProgress((p) => (p < 80 ? p + 10 : p));
    }, 200);

    try {
      const res = await studentsApi.import(importFile);
      setImportProgress(100);
      setImportResult(res.data.data);
      queryClient.invalidateQueries({ queryKey: ["students"] });
    } catch (err) {
      toast.error(getErrorMessage(err));
      setImportOpen(false);
    } finally {
      clearInterval(progressInterval);
      setImportLoading(false);
    }
  };

  const students = data?.data?.data ?? [];
  const pagination = data?.data?.pagination;

  // Bulk selection helpers
  const {
    selectedIds,
    toggleOne,
    toggleAll,
    clearSelection,
    isAllSelected: allSelected,
  } = useSelection(students, (s) => s.id);

  const someSelected = selectedIds.size > 0 && !allSelected;

  const colCount = isAdmin ? 8 : 6;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">O'quvchilar</h1>
          <p className="text-muted-foreground">
            {pagination?.total ?? 0} ta o'quvchi
          </p>
        </div>
        <div className="flex gap-2">
          <div className="flex rounded-md border">
            <Button
              variant={studentsView === "table" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-r-none border-0"
              onClick={() => setStudentsView("table")}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={studentsView === "card" ? "secondary" : "ghost"}
              size="sm"
              className="rounded-l-none border-0"
              onClick={() => setStudentsView("card")}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
          </div>
          {isAdmin && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setImportOpen(true)}
              >
                <Upload className="mr-2 h-4 w-4" />
                Yuklash
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleExport("xlsx")}
              >
                <Download className="mr-2 h-4 w-4" />
                Eksport
              </Button>
              <Button size="sm" onClick={() => setCreateOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Yangi
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Ism bo'yicha qidirish..."
            className="pl-9"
            value={searchInput}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setSearchInput(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <Select
          value={categoryFilter !== null ? String(categoryFilter) : "all"}
          onValueChange={(v) => {
            setCategoryFilter(v === "all" ? null : Number(v));
            setClassFilter("");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Barcha kategoriyalar" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Barcha kategoriyalar</SelectItem>
            {categories.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Bulk actions bar */}
      {selectedIds.size > 0 && isAdmin && (
        <div className="flex items-center gap-3 rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2">
          <span className="text-sm font-medium">
            {selectedIds.size} ta tanlandi
          </span>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => bulkDeleteMutation.mutate([...selectedIds] as string[])}
            disabled={bulkDeleteMutation.isPending}
          >
            {bulkDeleteMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
            O'chirish
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearSelection}
          >
            Bekor qilish
          </Button>
        </div>
      )}

      {/* Table or Card view */}
      {studentsView === "card" ? (
        isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-36 w-full" />
            ))}
          </div>
        ) : students.length === 0 ? (
          <p className="py-8 text-center text-muted-foreground">
            O'quvchilar topilmadi
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {students.map((s) => (
              <StudentCard
                key={s.id}
                student={s}
                isAdmin={isAdmin}
                onDelete={(id) => setDeleteId(id)}
              />
            ))}
          </div>
        )
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {isAdmin && (
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        allSelected
                          ? true
                          : someSelected
                            ? "indeterminate"
                            : false
                      }
                      onCheckedChange={(
                        checked: boolean | "indeterminate",
                      ) => toggleAll(checked === true)}
                    />
                  </TableHead>
                )}
                <TableHead>Ismi</TableHead>
                <TableHead>Kategoriya</TableHead>
                <TableHead>Xodim raqami</TableHead>
                <TableHead>Ota-ona telefoni</TableHead>
                <TableHead>Yuz</TableHead>
                <TableHead>Holat</TableHead>
                {isAdmin && <TableHead className="w-10" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: colCount }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-5 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
                : students.map((s) => (
                  <TableRow
                    key={s.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/students/${s.id}`)}
                  >
                    {isAdmin && (
                      <TableCell
                        onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      >
                        <Checkbox
                          checked={selectedIds.has(s.id)}
                          onCheckedChange={(
                            checked: boolean | "indeterminate",
                          ) => toggleOne(s.id, checked === true)}
                        />
                      </TableCell>
                    )}
                    <TableCell className="font-medium">{s.name}</TableCell>
                    <TableCell>{s.category?.name ?? s.class_name ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {s.employee_no}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {s.parent_phone || "—"}
                    </TableCell>
                    <TableCell>
                      {s.face_registered ? (
                        <Badge variant="default" className="gap-1">
                          <ScanFace className="h-3 w-3" />
                          Ha
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Yo'q</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={s.is_active ? "default" : "destructive"}
                      >
                        {s.is_active ? "Faol" : "Faol emas"}
                      </Badge>
                    </TableCell>
                    {isAdmin && (
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger
                            asChild
                            onClick={(e: React.MouseEvent) =>
                              e.stopPropagation()
                            }
                          >
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e: React.MouseEvent) => {
                                e.stopPropagation();
                                navigate(`/students/${s.id}`);
                              }}
                            >
                              <Pencil className="mr-2 h-4 w-4" />
                              Tahrirlash
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={(e: React.MouseEvent) => {
                                e.stopPropagation();
                                setDeleteId(s.id);
                              }}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              O'chirish
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              {!isLoading && students.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={colCount}
                    className="py-8 text-center text-muted-foreground"
                  >
                    O'quvchilar topilmadi
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Pagination with page numbers */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {(page - 1) * 20 + 1}–
            {Math.min(page * 20, pagination.total)}
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(1)}
            >
              &laquo;
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              Oldingi
            </Button>
            {(() => {
              const total = pagination.total_pages;
              const start = Math.max(1, Math.min(page - 2, total - 4));
              const end = Math.min(total, start + 4);
              return Array.from(
                { length: end - start + 1 },
                (_, i) => start + i,
              ).map((p) => (
                <Button
                  key={p}
                  variant={p === page ? "default" : "outline"}
                  size="sm"
                  className="w-8 px-0"
                  onClick={() => setPage(p)}
                >
                  {p}
                </Button>
              ));
            })()}
            <Button
              variant="outline"
              size="sm"
              disabled={page >= pagination.total_pages}
              onClick={() => setPage(page + 1)}
            >
              Keyingi
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= pagination.total_pages}
              onClick={() => setPage(pagination.total_pages)}
            >
              &raquo;
            </Button>
          </div>
        </div>
      )}

      {/* Create dialog */}
      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          if (!createMutation.isPending) {
            setCreateOpen(open);
            if (!open) {
              setFormData({ name: "", class_name: "", employee_no: "" });
              setFormErrors({});
            }
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi o'quvchi</DialogTitle>
            <DialogDescription>
              O'quvchi ma'lumotlarini kiriting
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Ismi *</Label>
              <Input
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setFormData({ ...formData, name: e.target.value });
                  if (formErrors.name) setFormErrors({ ...formErrors, name: "" });
                }}
              />
              {formErrors.name && (
                <p className="text-sm text-destructive">{formErrors.name}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Xodim raqami *</Label>
              <Input
                value={formData.employee_no ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setFormData({ ...formData, employee_no: e.target.value });
                  if (formErrors.employee_no) setFormErrors({ ...formErrors, employee_no: "" });
                }}
                placeholder="12345"
              />
              {formErrors.employee_no && (
                <p className="text-sm text-destructive">{formErrors.employee_no}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Kategoriya</Label>
              <Select
                value={formData.category_id ? String(formData.category_id) : "none"}
                onValueChange={(v) => {
                  const catId = v === "none" ? undefined : Number(v);
                  const catName = categories.find((c) => c.id === catId)?.name ?? "";
                  setFormData({ ...formData, category_id: catId, class_name: catName });
                  if (formErrors.class_name) setFormErrors({ ...formErrors, class_name: "" });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Kategoriya tanlang" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— Kategoriya yo'q</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!formData.category_id && (
                <Input
                  value={formData.class_name ?? ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    setFormData({ ...formData, class_name: e.target.value });
                    if (formErrors.class_name) setFormErrors({ ...formErrors, class_name: "" });
                  }}
                  placeholder="Yoki qo'lda kiriting: 7-A"
                />
              )}
              {formErrors.class_name && (
                <p className="text-sm text-destructive">{formErrors.class_name}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Ota-ona telefoni</Label>
              <Input
                value={formData.parent_phone ?? ""}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, parent_phone: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleCreateSubmit}
              disabled={createMutation.isPending}
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
      <AlertDialog
        open={deleteId !== null}
        onOpenChange={(open: boolean) => {
          if (!open) setDeleteId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>O'quvchini o'chirish</AlertDialogTitle>
            <AlertDialogDescription>
              Bu amalni bekor qilib bo'lmaydi. O'quvchi va uning barcha
              davomat yozuvlari butunlay o'chiriladi.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => {
                if (deleteId) {
                  deleteMutation.mutate(deleteId);
                  setDeleteId(null);
                }
              }}
            >
              O'chirish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Import dialog */}
      <Dialog
        open={importOpen}
        onOpenChange={(open: boolean) => {
          if (!open) {
            setImportOpen(false);
            setImportFile(null);
            setImportProgress(0);
            setImportResult(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>O'quvchilarni yuklash</DialogTitle>
            <DialogDescription>
              Excel (.xlsx) fayl yuklang. Ustunlar: name,
              class_name, phone, parent_phone, employee_no.
            </DialogDescription>
          </DialogHeader>

          {importResult ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold text-green-600">
                    {importResult.created}
                  </p>
                  <p className="text-xs text-muted-foreground">Yaratildi</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold text-blue-600">
                    {importResult.updated}
                  </p>
                  <p className="text-xs text-muted-foreground">Yangilandi</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold">{importResult.total}</p>
                  <p className="text-xs text-muted-foreground">Jami</p>
                </div>
              </div>
              {importResult.errors.length > 0 && (
                <div className="space-y-1 rounded-md border border-destructive/40 bg-destructive/5 p-3">
                  <p className="text-sm font-medium text-destructive">
                    {importResult.errors.length} ta xato:
                  </p>
                  <div className="max-h-32 space-y-0.5 overflow-y-auto">
                    {importResult.errors.map((err, i) => (
                      <p key={i} className="text-xs text-muted-foreground">
                        {err}
                      </p>
                    ))}
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button
                  onClick={() => {
                    setImportOpen(false);
                    setImportFile(null);
                    setImportProgress(0);
                    setImportResult(null);
                  }}
                >
                  Yopish
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6">
                <Upload className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Excel faylni tanlang
                </p>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  id="import-file-input"
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    setImportFile(e.target.files?.[0] ?? null);
                  }}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    document.getElementById("import-file-input")?.click()
                  }
                >
                  Fayl tanlash
                </Button>
                {importFile && (
                  <p className="text-sm font-medium">{importFile.name}</p>
                )}
              </div>

              {importLoading && (
                <div className="space-y-2">
                  <Progress value={importProgress} />
                  <p className="text-center text-xs text-muted-foreground">
                    Yuklanmoqda... {importProgress}%
                  </p>
                </div>
              )}

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setImportOpen(false)}
                  disabled={importLoading}
                >
                  Bekor qilish
                </Button>
                <Button
                  onClick={handleImport}
                  disabled={!importFile || importLoading}
                >
                  {importLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Yuklash
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
