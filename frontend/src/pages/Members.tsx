import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  FolderOpen,
  Users,
  FolderPlus,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  ArrowUpDown,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
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

import { studentsApi } from "@/services/studentsApi";
import { categoriesApi } from "@/services/categoriesApi";
import { getErrorMessage } from "@/services/api";
import type { Category, CategoryCreate, CategoryUpdate, StudentCreate, StudentImportResult } from "@/types";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { useDebounce } from "@/hooks/useDebounce";
import { useCategories, useCreateCategory, useUpdateCategory, useDeleteCategory } from "@/hooks/useCategories";
import { StudentCard } from "@/components/students/StudentCard";
import { useSelection } from "@/hooks/useSelection";
import { EmptyState } from "@/components/common/EmptyState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";

// ─── Category Grid Card ────────────────────────────────────────────────────
function CategoryCard({
  category,
  isAdmin,
  onEdit,
  onDelete,
}: {
  category: Category;
  isAdmin: boolean;
  onEdit: (c: Category) => void;
  onDelete: (c: Category) => void;
}) {
  const navigate = useNavigate();
  const { data: statsData } = useQuery({
    queryKey: ["category-stats", category.id],
    queryFn: () => categoriesApi.stats(category.id),
    staleTime: 60_000,
  });
  const stats = statsData?.data?.data;

  return (
    <div
      className="group flex flex-col gap-3 rounded-2xl border border-border/50 bg-white/40 dark:bg-slate-900/40 backdrop-blur-md p-5 cursor-pointer hover:border-primary/50 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 premium-shadow"
      onClick={() => navigate(`/students/category/${category.id}`)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
            <FolderOpen className="h-5 w-5 text-primary" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold leading-tight truncate">{category.name}</p>
            {category.description && (
              <p className="text-xs text-muted-foreground truncate">{category.description}</p>
            )}
          </div>
        </div>
        {isAdmin && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 flex-shrink-0 opacity-0 group-hover:opacity-100"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(category);
                }}
              >
                <Pencil className="mr-2 h-4 w-4" />
                Tahrirlash
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(category);
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                O'chirish
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          {stats !== undefined ? (
            <>
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {stats.active} ta o'quvchi
              </span>
              {stats.children > 0 && (
                <span className="flex items-center gap-1">
                  <FolderOpen className="h-3.5 w-3.5" />
                  {stats.children} ta pastki guruh
                </span>
              )}
            </>
          ) : (
            <Skeleton className="h-4 w-24" />
          )}
        </div>
        <span className="text-xs text-muted-foreground/50 group-hover:text-primary transition-colors font-medium">
          Ochish →
        </span>
      </div>
    </div>
  );
}


// ─── Main Members Page ──────────────────────────────────────────────────────
export default function Members() {
  const { categoryId: categoryIdStr } = useParams<{ categoryId?: string }>();
  const categoryId = categoryIdStr ? Number(categoryIdStr) : undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "super_admin" || user?.role === "admin";
  const { studentsView, setStudentsView } = useUIStore();

  // Category management state
  const [createCatOpen, setCreateCatOpen] = useState(false);
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [deleteCategory, setDeleteCategory] = useState<Category | null>(null);
  const [catForm, setCatForm] = useState<CategoryCreate>({ name: "", description: "" });
  const [editCatForm, setEditCatForm] = useState<CategoryUpdate>({});

  const createCatMutation = useCreateCategory();
  const updateCatMutation = useUpdateCategory();
  const deleteCatMutation = useDeleteCategory();

  // Fetch sub-categories (children of current category, or top-level if none)
  const parentFilter = categoryId !== undefined ? categoryId : 0;
  const { data: catsData, isLoading: catsLoading } = useCategories(parentFilter);
  const subCategories: Category[] = catsData?.data?.data ?? [];

  // Fetch all categories for student create dropdown
  const { data: allCatsData } = useCategories();
  const allCategories: Category[] = allCatsData?.data?.data ?? [];

  // Student state
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 300);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [createStudentOpen, setCreateStudentOpen] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<StudentCreate>({
    name: "",
    class_name: "",
    employee_no: "",
    category_id: categoryId,
  });

  // Move state
  const [moveOpen, setMoveOpen] = useState(false);
  const [moveToCategoryId, setMoveToCategoryId] = useState<string>("");

  // Sort state
  const [sort, setSort] = useState("-created_at");

  // Import state
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importProgress, setImportProgress] = useState(0);
  const [importResult, setImportResult] = useState<StudentImportResult | null>(null);
  const [importLoading, setImportLoading] = useState(false);

  // Students query — only show if we're inside a category
  const { data: studentsData, isLoading: studentsLoading } = useQuery({
    queryKey: ["students", page, search, categoryId, sort],
    queryFn: () =>
      studentsApi.list({
        page,
        per_page: 24,
        search: search || undefined,
        category_id: categoryId,
        sort,
      }),
    enabled: categoryId !== undefined,
    staleTime: 0,
  });

  const students = studentsData?.data?.data ?? [];
  const pagination = studentsData?.data?.pagination;

  const {
    selectedIds,
    toggleOne,
    toggleAll,
    clearSelection,
    isAllSelected: allSelected,
  } = useSelection(students, (s) => s.id);
  const someSelected = selectedIds.size > 0 && !allSelected;
  const colCount = isAdmin ? 8 : 6;

  // Category handlers
  const handleCreateCategory = () => {
    if (!catForm.name.trim()) return;
    createCatMutation.mutate(
      { ...catForm, parent_id: categoryId ?? null },
      {
        onSuccess: () => {
          setCreateCatOpen(false);
          setCatForm({ name: "", description: "" });
        },
      },
    );
  };

  const openEditCat = (c: Category) => {
    setEditCategory(c);
    setEditCatForm({ name: c.name, description: c.description ?? "" });
  };

  const handleUpdateCategory = () => {
    if (!editCategory) return;
    updateCatMutation.mutate(
      { id: editCategory.id, data: editCatForm },
      { onSuccess: () => setEditCategory(null) },
    );
  };

  // Student handlers
  const createStudentMutation = useMutation({
    mutationFn: (data: StudentCreate) => studentsApi.create(data),
    onSuccess: () => {
      toast.success("O'quvchi yaratildi");
      setCreateStudentOpen(false);
      setFormData({ name: "", class_name: "", employee_no: "", category_id: categoryId });
      setFormErrors({});
      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["category-stats"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const deleteStudentMutation = useMutation({
    mutationFn: (id: string) => studentsApi.delete(id),
    onSuccess: () => {
      toast.success("O'quvchi o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: string[]) => Promise.all(ids.map((id) => studentsApi.delete(id))),
    onSuccess: () => {
      toast.success(`${selectedIds.size} ta o'quvchi o'chirildi`);
      clearSelection();
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const bulkMoveMutation = useMutation({
    mutationFn: ({ ids, targetCategoryId }: { ids: string[]; targetCategoryId: number | null }) =>
      Promise.all(ids.map((id) => studentsApi.update(id, { category_id: targetCategoryId ?? undefined }))),
    onSuccess: () => {
      const targetName = allCategories.find((c) => c.id === Number(moveToCategoryId))?.name ?? "kategoriyasiz";
      toast.success(`${selectedIds.size} ta o'quvchi "${targetName}" ga ko'chirildi`);
      clearSelection();
      setMoveOpen(false);
      setMoveToCategoryId("");
      setPage(1);
      queryClient.invalidateQueries({ queryKey: ["students"], refetchType: "all" });
      queryClient.invalidateQueries({ queryKey: ["categories"], refetchType: "all" });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleImport = async () => {
    if (!importFile) return;
    setImportLoading(true);
    setImportProgress(0);
    setImportResult(null);
    const interval = setInterval(() => setImportProgress((p) => (p < 80 ? p + 10 : p)), 200);
    try {
      const res = await studentsApi.import(importFile);
      setImportProgress(100);
      setImportResult(res.data.data);
      queryClient.invalidateQueries({ queryKey: ["students"] });
    } catch (err) {
      toast.error(getErrorMessage(err));
      setImportOpen(false);
    } finally {
      clearInterval(interval);
      setImportLoading(false);
    }
  };

  const handleStudentCreate = () => {
    const errors: Record<string, string> = {};
    if (!formData.name.trim()) errors.name = "Ism kiritilishi shart";
    if (!formData.employee_no?.trim()) errors.employee_no = "ID raqam kiritilishi shart";
    if (!formData.category_id && !formData.class_name?.trim())
      errors.class_name = "Guruh yoki sinf kiritilishi shart";
    if (Object.keys(errors).length > 0) { setFormErrors(errors); return; }
    setFormErrors({});
    createStudentMutation.mutate(formData);
  };

  // ── Page title
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {categoryId && (
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
          )}
          {!categoryId && (
            <h1 className="text-2xl font-bold tracking-tight">O'quvchilar</h1>
          )}
        </div>
        <div className="flex gap-2">
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCatForm({ name: "", description: "" });
                setCreateCatOpen(true);
              }}
            >
              <FolderPlus className="mr-2 h-4 w-4" />
              Yangi guruh
            </Button>
          )}
          {categoryId !== undefined && isAdmin && (
            <>
              <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Yuklash
              </Button>
              <Button size="sm" onClick={() => {
                setFormData({ name: "", class_name: "", employee_no: "", category_id: categoryId });
                setFormErrors({});
                setCreateStudentOpen(true);
              }}>
                <Plus className="mr-2 h-4 w-4" />
                Yangi o'quvchi
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Sub-categories grid */}
      {(subCategories.length > 0 || catsLoading) && (
        <div>
          {categoryId && (
            <p className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Pastki guruhlar
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {catsLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full rounded-xl" />
                ))
              : subCategories.map((cat) => (
                  <CategoryCard
                    key={cat.id}
                    category={cat}
                    isAdmin={isAdmin}
                    onEdit={openEditCat}
                    onDelete={setDeleteCategory}
                  />
                ))}
          </div>
        </div>
      )}

      {/* Empty state (no categories, not inside a category) */}
      {!catsLoading && subCategories.length === 0 && categoryId === undefined && (
        <EmptyState
          icon={FolderOpen}
          title="Guruhlar topilmadi"
          description={isAdmin ? "Birinchi guruhni yarating" : "Guruhlar mavjud emas"}
        />
      )}

      {/* Student list — only inside a category */}
      {categoryId !== undefined && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              O'quvchilar ({pagination?.total ?? 0})
            </p>
            <div className="flex items-center gap-2">
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      const res = await studentsApi.export({ format: "xlsx", category_id: categoryId });
                      const url = window.URL.createObjectURL(new Blob([res.data]));
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "members.xlsx";
                      a.click();
                      window.URL.revokeObjectURL(url);
                    } catch (err) {
                      toast.error(getErrorMessage(err));
                    }
                  }}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Eksport
                </Button>
              )}
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Ism bo'yicha qidirish..."
              className="pl-9"
              value={searchInput}
              onChange={(e) => { setSearchInput(e.target.value); setPage(1); }}
            />
          </div>

          {/* Bulk actions */}
          {selectedIds.size > 0 && isAdmin && (
            <div className="flex items-center gap-3 rounded-md border bg-muted/50 px-3 py-2">
              <span className="text-sm font-medium">{selectedIds.size} ta tanlandi</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setMoveOpen(true)}
              >
                <FolderOpen className="mr-2 h-4 w-4" />
                Ko'chirish
              </Button>
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
              <Button variant="ghost" size="sm" onClick={clearSelection}>
                Bekor qilish
              </Button>
            </div>
          )}

          {/* Table / Card view */}
          {studentsView === "card" ? (
            studentsLoading ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-36 w-full" />
                ))}
              </div>
            ) : students.length === 0 ? (
              <EmptyState icon={Users} title="O'quvchilar topilmadi" description="Bu guruhda hali o'quvchilar yo'q" />
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {students.map((s) => (
                  <StudentCard key={s.id} student={s} isAdmin={isAdmin} onDelete={setDeleteId} />
                ))}
              </div>
            )
          ) : (
            <div className="rounded-xl border border-border/50 bg-white/40 dark:bg-slate-950/40 backdrop-blur-md shadow-inner overflow-hidden">
              <Table>
                <TableHeader className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-border/50">
                  <TableRow className="hover:bg-transparent">
                    {isAdmin && (
                      <TableHead className="w-10">
                        <Checkbox
                          checked={allSelected ? true : someSelected ? "indeterminate" : false}
                          onCheckedChange={(checked) => toggleAll(checked === true)}
                        />
                      </TableHead>
                    )}
                    {(
                      [
                        { label: "Ismi", field: "name" },
                        { label: "Guruh", field: "class_name" },
                        { label: "Xodim raqami", field: "employee_no" },
                        { label: "Ota-ona telefoni", field: "parent_phone" },
                        { label: "Yuz", field: "face_registered" },
                        { label: "Holat", field: "is_active" },
                      ] as { label: string; field: string }[]
                    ).map(({ label, field }) => {
                      const isActive = sort === field || sort === `-${field}`;
                      const isDesc = sort === `-${field}`;
                      return (
                        <TableHead
                          key={field}
                          className="cursor-pointer select-none hover:text-foreground"
                          onClick={() => setSort(isActive && !isDesc ? `-${field}` : field)}
                        >
                          <span className="flex items-center gap-1">
                            {label}
                            {isActive ? (
                              isDesc ? <ArrowDown className="h-3.5 w-3.5 text-primary" /> : <ArrowUp className="h-3.5 w-3.5 text-primary" />
                            ) : (
                              <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground/50" />
                            )}
                          </span>
                        </TableHead>
                      );
                    })}
                    {isAdmin && <TableHead className="w-10" />}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {studentsLoading
                    ? Array.from({ length: 5 }).map((_, i) => (
                        <TableRow key={i}>
                          {Array.from({ length: colCount }).map((_, j) => (
                            <TableCell key={j}><Skeleton className="h-5 w-full" /></TableCell>
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
                            <TableCell onClick={(e) => e.stopPropagation()}>
                              <Checkbox
                                checked={selectedIds.has(s.id)}
                                onCheckedChange={(checked) => toggleOne(s.id, checked === true)}
                              />
                            </TableCell>
                          )}
                          <TableCell className="font-medium">{s.name}</TableCell>
                          <TableCell>{s.category?.name ?? s.class_name ?? "—"}</TableCell>
                          <TableCell className="text-muted-foreground">{s.employee_no}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {s.parent_phone || "—"}
                          </TableCell>
                          <TableCell>
                            {s.face_registered ? (
                              <Badge variant="default" className="gap-1">
                                <ScanFace className="h-3 w-3" />Ha
                              </Badge>
                            ) : (
                              <Badge variant="secondary">Yo'q</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant={s.is_active ? "default" : "destructive"}>
                              {s.is_active ? "Faol" : "Faol emas"}
                            </Badge>
                          </TableCell>
                          {isAdmin && (
                            <TableCell>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                                  <Button variant="ghost" size="icon">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem
                                    onClick={(e) => { e.stopPropagation(); navigate(`/students/${s.id}`); }}
                                  >
                                    <Pencil className="mr-2 h-4 w-4" />
                                    Tahrirlash
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    className="text-destructive"
                                    onClick={(e) => { e.stopPropagation(); setDeleteId(s.id); }}
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
                  {!studentsLoading && students.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={colCount} className="py-8 text-center text-muted-foreground">
                        O'quvchilar topilmadi
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {(page - 1) * 20 + 1}–{Math.min(page * 20, pagination.total)} / {pagination.total}
              </p>
              <div className="flex items-center gap-1">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(1)}>
                  &laquo;
                </Button>
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  Oldingi
                </Button>
                {(() => {
                  const total = pagination.total_pages;
                  const start = Math.max(1, Math.min(page - 2, total - 4));
                  const end = Math.min(total, start + 4);
                  return Array.from({ length: end - start + 1 }, (_, i) => start + i).map((p) => (
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
        </>
      )}

      {/* ── Dialogs ── */}

      {/* Create category dialog */}
      <Dialog
        open={createCatOpen}
        onOpenChange={(open) => {
          if (!createCatMutation.isPending) {
            setCreateCatOpen(open);
            if (!open) setCatForm({ name: "", description: "" });
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi guruh</DialogTitle>
            <DialogDescription>
              {categoryId ? "Pastki guruh yarating" : "Asosiy guruh yarating"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Ismi *</Label>
              <Input
                value={catForm.name}
                onChange={(e) => setCatForm({ ...catForm, name: e.target.value })}
                placeholder="masalan: 7-A, O'qituvchilar, IT bo'lim"
              />
            </div>
            <div className="space-y-2">
              <Label>Tavsif</Label>
              <Input
                value={catForm.description ?? ""}
                onChange={(e) => setCatForm({ ...catForm, description: e.target.value })}
                placeholder="Ixtiyoriy"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateCatOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleCreateCategory}
              disabled={createCatMutation.isPending || !catForm.name.trim()}
            >
              {createCatMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Yaratish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit category dialog */}
      <Dialog
        open={editCategory !== null}
        onOpenChange={(open) => !open && setEditCategory(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Guruhni tahrirlash</DialogTitle>
            <DialogDescription>{editCategory?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Ismi *</Label>
              <Input
                value={editCatForm.name ?? ""}
                onChange={(e) => setEditCatForm({ ...editCatForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Tavsif</Label>
              <Input
                value={editCatForm.description ?? ""}
                onChange={(e) => setEditCatForm({ ...editCatForm, description: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditCategory(null)}>
              Bekor qilish
            </Button>
            <Button
              onClick={handleUpdateCategory}
              disabled={updateCatMutation.isPending || !editCatForm.name?.trim()}
            >
              {updateCatMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Saqlash
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete category confirm */}
      <ConfirmDialog
        open={deleteCategory !== null}
        onOpenChange={(open) => !open && setDeleteCategory(null)}
        title={`"${deleteCategory?.name}" o'chirilsinmi?`}
        description="Guruh o'chiriladi. Undagi pastki guruhlar va o'quvchilar guruhsiz qoladi."
        variant="destructive"
        confirmLabel="O'chirish"
        onConfirm={() => {
          if (deleteCategory) {
            deleteCatMutation.mutate(deleteCategory.id);
            setDeleteCategory(null);
          }
        }}
      />

      {/* Create student dialog */}
      <Dialog
        open={createStudentOpen}
        onOpenChange={(open) => {
          if (!createStudentMutation.isPending) {
            setCreateStudentOpen(open);
            if (!open) {
              setFormData({ name: "", class_name: "", employee_no: "", category_id: categoryId });
              setFormErrors({});
            }
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi o'quvchi</DialogTitle>
            <DialogDescription>O'quvchi ma'lumotlarini kiriting</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Ismi *</Label>
              <Input
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  if (formErrors.name) setFormErrors({ ...formErrors, name: "" });
                }}
              />
              {formErrors.name && <p className="text-sm text-destructive">{formErrors.name}</p>}
            </div>
            <div className="space-y-2">
              <Label>ID raqam (Employee No) *</Label>
              <Input
                value={formData.employee_no ?? ""}
                onChange={(e) => {
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
              <Label>Guruh</Label>
              <Select
                value={formData.category_id ? String(formData.category_id) : "none"}
                onValueChange={(v) => {
                  const catId = v === "none" ? undefined : Number(v);
                  const catName = allCategories.find((c) => c.id === catId)?.name ?? "";
                  setFormData({ ...formData, category_id: catId, class_name: catName });
                  if (formErrors.class_name) setFormErrors({ ...formErrors, class_name: "" });
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Guruhni tanlang" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— Guruhsiz</SelectItem>
                  {allCategories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!formData.category_id && (
                <Input
                  value={formData.class_name ?? ""}
                  onChange={(e) => {
                    setFormData({ ...formData, class_name: e.target.value });
                    if (formErrors.class_name) setFormErrors({ ...formErrors, class_name: "" });
                  }}
                  placeholder="Qo'lda kiriting: 7-A"
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
                onChange={(e) => setFormData({ ...formData, parent_phone: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateStudentOpen(false)}>
              Bekor qilish
            </Button>
            <Button onClick={handleStudentCreate} disabled={createStudentMutation.isPending}>
              {createStudentMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Saqlash
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete student confirm */}
      <AlertDialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>O'quvchini o'chirish</AlertDialogTitle>
            <AlertDialogDescription>
              Bu amalni qaytarib bo'lmaydi. O'quvchi va uning barcha davomat yozuvlari o'chiriladi.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => { if (deleteId) { deleteStudentMutation.mutate(deleteId); setDeleteId(null); } }}
            >
              O'chirish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Import dialog */}
      <Dialog
        open={importOpen}
        onOpenChange={(open) => {
          if (!open) { setImportOpen(false); setImportFile(null); setImportProgress(0); setImportResult(null); }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>O'quvchilarni import qilish</DialogTitle>
            <DialogDescription>
              Excel (.xlsx) faylini yuklang. Ustunlar: name, class_name, phone, parent_phone, employee_no.
            </DialogDescription>
          </DialogHeader>
          {importResult ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold text-green-600">{importResult.created}</p>
                  <p className="text-xs text-muted-foreground">Yaratildi</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold text-blue-600">{importResult.updated}</p>
                  <p className="text-xs text-muted-foreground">Yangilandi</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-2xl font-bold">{importResult.total}</p>
                  <p className="text-xs text-muted-foreground">Jami</p>
                </div>
              </div>
              {importResult.errors.length > 0 && (
                <div className="space-y-1 rounded-md border border-destructive/40 bg-destructive/5 p-3">
                  <p className="text-sm font-medium text-destructive">{importResult.errors.length} ta xato:</p>
                  <div className="max-h-32 space-y-0.5 overflow-y-auto">
                    {importResult.errors.map((err, i) => (
                      <p key={i} className="text-xs text-muted-foreground">{err}</p>
                    ))}
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button onClick={() => { setImportOpen(false); setImportFile(null); setImportProgress(0); setImportResult(null); }}>
                  Yopish
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6">
                <Upload className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">Excel faylini tanlang</p>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  className="hidden"
                  id="import-file-input"
                  onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
                />
                <Button variant="outline" size="sm" onClick={() => document.getElementById("import-file-input")?.click()}>
                  Fayl tanlash
                </Button>
                {importFile && <p className="text-sm font-medium">{importFile.name}</p>}
              </div>
              {importLoading && (
                <div className="space-y-2">
                  <Progress value={importProgress} />
                  <p className="text-center text-xs text-muted-foreground">Yuklanmoqda... {importProgress}%</p>
                </div>
              )}
              <DialogFooter>
                <Button variant="outline" onClick={() => setImportOpen(false)} disabled={importLoading}>
                  Bekor qilish
                </Button>
                <Button onClick={handleImport} disabled={!importFile || importLoading}>
                  {importLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
                  Import qilish
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Ko'chirish modali */}
      <Dialog open={moveOpen} onOpenChange={setMoveOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Guruhga ko'chirish</DialogTitle>
            <DialogDescription>
              {selectedIds.size} ta o'quvchini qaysi guruhga ko'chirmoqchisiz?
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Select value={moveToCategoryId} onValueChange={setMoveToCategoryId}>
              <SelectTrigger>
                <SelectValue placeholder="Guruh tanlang..." />
              </SelectTrigger>
              <SelectContent>
                {allCategories
                  .filter((c) => c.id !== categoryId)
                  .map((cat) => (
                    <SelectItem key={cat.id} value={String(cat.id)}>
                      {cat.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMoveOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              disabled={!moveToCategoryId || bulkMoveMutation.isPending}
              onClick={() =>
                bulkMoveMutation.mutate({
                  ids: [...selectedIds] as string[],
                  targetCategoryId: Number(moveToCategoryId),
                })
              }
            >
              {bulkMoveMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FolderOpen className="mr-2 h-4 w-4" />
              )}
              Ko'chirish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
