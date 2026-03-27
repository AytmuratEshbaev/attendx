import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { devicesApi } from "@/services/devicesApi";
import { categoriesApi } from "@/services/categoriesApi";
import { studentsApi } from "@/services/studentsApi";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  Monitor,
  Download,
  CheckCircle2,
  SkipForward,
  AlertCircle,
  Loader2,
  Wifi,
  WifiOff,
  ExternalLink,
  Trash2,
  Users,
} from "lucide-react";

interface ImportResult {
  total: number;
  created: number;
  skipped: number;
  errors: string[];
}

export default function ImportPersons() {
  const [categoryId, setCategoryId] = useState<string>("none");
  const [results, setResults] = useState<Record<number, ImportResult>>({});
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data: devicesData, isLoading: devicesLoading } = useQuery({
    queryKey: ["devices"],
    queryFn: () => devicesApi.list(),
  });

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });

  // Kategoriyasiz o'quvchilar
  const { data: uncategorizedData, isLoading: uncatLoading, refetch: refetchUncat } = useQuery({
    queryKey: ["students", "no_category"],
    queryFn: () => studentsApi.list({ no_category: true, per_page: 100 }),
  });

  const devices = devicesData?.data?.data ?? [];
  const categories = categoriesData?.data?.data ?? [];
  const uncategorized = uncategorizedData?.data?.data ?? [];
  const uncatTotal = uncategorizedData?.data?.pagination?.total ?? 0;

  const importMutation = useMutation({
    mutationFn: (deviceId: number) =>
      devicesApi.importPersons(deviceId, categoryId !== "none" ? Number(categoryId) : undefined),
    onSuccess: (res, deviceId) => {
      const result = res.data.data;
      setResults((prev) => ({ ...prev, [deviceId]: result }));
      toast.success(`Import tugadi: ${result.created} ta yangi o'quvchi qo'shildi`);
      refetchUncat();
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? "Qurilmaga ulanib bo'lmadi";
      toast.error(`Xatolik: ${msg}`);
    },
  });

  const deleteOne = async (id: string, name: string) => {
    setDeletingIds((s) => new Set(s).add(id));
    try {
      await studentsApi.delete(id);
      toast.success(`${name} o'chirildi`);
      refetchUncat();
      queryClient.invalidateQueries({ queryKey: ["students"] });
    } catch {
      toast.error("O'chirishda xatolik");
    } finally {
      setDeletingIds((s) => { const n = new Set(s); n.delete(id); return n; });
    }
  };

  const deleteAll = async () => {
    if (!uncategorized.length) return;
    const ids = uncategorized.map((s) => s.id);
    for (const id of ids) {
      try { await studentsApi.delete(id); } catch { /* ignore */ }
    }
    toast.success(`${ids.length} ta o'quvchi o'chirildi`);
    refetchUncat();
    queryClient.invalidateQueries({ queryKey: ["students"] });
  };

  const studentsLink =
    categoryId !== "none" ? `/students/category/${categoryId}` : "/students";

  const totalCreated = Object.values(results).reduce((s, r) => s + r.created, 0);

  if (devicesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Qurilmadan import</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Hikvision qurilmalaridagi shaxslarni o'quvchilar ro'yxatiga import qilish
          </p>
        </div>
        {devices.length > 1 && (
          <Button
            onClick={() => devices.forEach((d) => importMutation.mutate(d.id))}
            disabled={importMutation.isPending}
          >
            {importMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Barchasidan import
          </Button>
        )}
      </div>

      {/* Kategoriyasiz o'quvchilar */}
      {(uncatLoading || uncatTotal > 0) && (
        <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-amber-600" />
                <CardTitle className="text-base text-amber-800 dark:text-amber-400">
                  Kategoriyasiz o'quvchilar
                </CardTitle>
                {!uncatLoading && (
                  <Badge variant="outline" className="border-amber-300 text-amber-700">
                    {uncatTotal} ta
                  </Badge>
                )}
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={deleteAll}
                disabled={uncatLoading || uncatTotal === 0}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Barchasini o'chirish
              </Button>
            </div>
            <CardDescription>
              Avval import qilingan, lekin kategoriyaga biriktirilmagan o'quvchilar
            </CardDescription>
          </CardHeader>
          <CardContent>
            {uncatLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Yuklanmoqda...
              </div>
            ) : (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {uncategorized.map((student) => (
                  <div
                    key={student.id}
                    className="flex items-center justify-between rounded-md px-2 py-1 hover:bg-amber-100/50 dark:hover:bg-amber-900/20"
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium">{student.name}</span>
                      {student.employee_no && (
                        <span className="text-xs text-muted-foreground">
                          #{student.employee_no}
                        </span>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive hover:text-destructive"
                      disabled={deletingIds.has(student.id)}
                      onClick={() => deleteOne(student.id, student.name)}
                    >
                      {deletingIds.has(student.id) ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Kategoriya tanlash */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Kategoriya (ixtiyoriy)</CardTitle>
          <CardDescription>
            Import qilingan o'quvchilar qaysi kategoriyaga biriktirilsin?
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Kategoriyasiz" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Kategoriyasiz</SelectItem>
              {categories.map((cat) => (
                <SelectItem key={cat.id} value={String(cat.id)}>
                  {cat.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {totalCreated > 0 && (
            <Button variant="outline" size="sm" asChild>
              <Link to={studentsLink}>
                <ExternalLink className="h-4 w-4 mr-2" />
                {totalCreated} ta yangi o'quvchini ko'rish
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Qurilmalar */}
      {devices.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Monitor className="h-12 w-12 mb-4 opacity-30" />
            <p>Hech qanday qurilma topilmadi</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {devices.map((device) => {
            const res = results[device.id];
            const isPending =
              importMutation.isPending && importMutation.variables === device.id;

            return (
              <Card key={device.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Monitor className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-base">{device.name}</CardTitle>
                    </div>
                    {device.is_active ? (
                      <Badge variant="outline" className="text-green-600 border-green-200">
                        <Wifi className="h-3 w-3 mr-1" />
                        Faol
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-500 border-red-200">
                        <WifiOff className="h-3 w-3 mr-1" />
                        Nofaol
                      </Badge>
                    )}
                  </div>
                  <CardDescription className="text-xs">
                    {device.ip_address}:{device.port}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-3">
                  {res ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Jami topildi</span>
                        <span className="font-medium">{res.total} ta</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1 text-green-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Yangi qo'shildi
                        </span>
                        <span className="font-medium text-green-600">{res.created} ta</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <SkipForward className="h-3.5 w-3.5" />
                          Mavjud edi
                        </span>
                        <span className="font-medium">{res.skipped} ta</span>
                      </div>
                      {res.errors.length > 0 && (
                        <div className="rounded-md bg-destructive/10 p-2 text-xs text-destructive space-y-1">
                          <div className="flex items-center gap-1 font-medium">
                            <AlertCircle className="h-3.5 w-3.5" />
                            Xatoliklar ({res.errors.length})
                          </div>
                          {res.errors.slice(0, 3).map((e, i) => (
                            <div key={i} className="truncate">{e}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Import hali amalga oshirilmagan
                    </p>
                  )}

                  <Button
                    className="w-full"
                    variant={res ? "outline" : "default"}
                    disabled={isPending || !device.is_active}
                    onClick={() => importMutation.mutate(device.id)}
                  >
                    {isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Yuklanmoqda...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        {res ? "Qayta import" : "Import qilish"}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
