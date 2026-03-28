import { useState } from "react";
import { toast } from "sonner";
import {
  Download,
  Loader2,
  FileSpreadsheet,
  CalendarDays,
  CalendarRange,
  Calendar,
  History,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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

import { useQuery } from "@tanstack/react-query";
import { attendanceApi } from "@/services/attendanceApi";
import { studentsApi } from "@/services/studentsApi";
import { getErrorMessage } from "@/services/api";
import { useDownload } from "@/hooks/useDownload";
import { useReportHistory } from "@/hooks/useReportHistory";
import { PageHeader } from "@/components/common/PageHeader";
import { DateRangePicker } from "@/components/common/DateRangePicker";

export default function Reports() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [format, setFormat] = useState("xlsx");
  const [loading, setLoading] = useState(false);
  const [quickLoading, setQuickLoading] = useState<string | null>(null);

  const { reportHistory, addReportHistory, clearReportHistory } = useReportHistory();
  const { download } = useDownload();

  const { data: classesRes } = useQuery({
    queryKey: ["student-classes"],
    queryFn: () => studentsApi.classes(),
    staleTime: 5 * 60 * 1000,
  });
  const classList = classesRes?.data?.data ?? [];

  const fmt = (d: Date) => d.toISOString().split("T")[0];

  const doDownload = async (
    from: string,
    to: string,
    fmt_: string,
    cls?: string,
    reportName?: string,
  ) => {
    try {
      const res = await attendanceApi.report({
        date_from: from,
        date_to: to,
        class_name: cls || undefined,
        format: fmt_,
      });
      const filename = `attendance-${from}-${to}.${fmt_}`;
      download(new Blob([res.data]), filename);
      toast.success("Hisobot yuklandi");

      const item = {
        name: reportName || `${from} — ${to}`,
        dateFrom: from,
        dateTo: to,
        format: fmt_,
        downloadedAt: new Date().toISOString(),
      };
      addReportHistory(item);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleDownload = async () => {
    if (!dateFrom || !dateTo) {
      toast.error("Iltimos, sana oralig'ini tanlang");
      return;
    }
    setLoading(true);
    await doDownload(dateFrom, dateTo, format, classFilter);
    setLoading(false);
  };

  const handleQuickDownload = async (type: "daily" | "weekly" | "monthly") => {
    setQuickLoading(type);
    const today = new Date();
    let from = "";
    const to = fmt(new Date());
    let name = "";

    if (type === "daily") {
      from = fmt(today);
      name = "Kunlik hisobot";
    } else if (type === "weekly") {
      const day = today.getDay();
      const diff = day === 0 ? 6 : day - 1;
      const start = new Date(today);
      start.setDate(today.getDate() - diff);
      from = fmt(start);
      name = "Haftalik hisobot";
    } else {
      const start = new Date(today.getFullYear(), today.getMonth(), 1);
      from = fmt(start);
      name = "Oylik hisobot";
    }

    await doDownload(from, to, "xlsx", "", name);
    setQuickLoading(null);
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Hisobotlar"
        description="Davomat hisobotlarini yuklab olish"
      />

      {/* Quick action cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        {([
          { type: "daily" as const, title: "Kunlik", desc: "Bugungi davomat hisoboti", icon: CalendarDays },
          { type: "weekly" as const, title: "Haftalik", desc: "Bu haftalik hisobot", icon: CalendarRange },
          { type: "monthly" as const, title: "Oylik", desc: "Bu oylik hisobot", icon: Calendar },
        ]).map((item) => (
          <Card
            key={item.type}
            className="cursor-pointer glass-card border-none hover:border-primary/20 premium-shadow group"
            onClick={() => !quickLoading && handleQuickDownload(item.type)}
          >
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="rounded-xl bg-gradient-premium shadow-md shadow-primary/20 p-3 transition-transform group-hover:scale-110">
                <item.icon className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="font-semibold">{item.title}</p>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
              {quickLoading === item.type ? (
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              ) : (
                <Download className="h-5 w-5 text-muted-foreground" />
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Custom report builder */}
      <Card className="glass-card border-none premium-shadow">
        <CardHeader className="bg-white/30 dark:bg-slate-900/30 rounded-t-xl backdrop-blur-md border-b border-border/50 pb-4 mb-4">
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-primary" />
            Maxsus hisobot
          </CardTitle>
          <CardDescription>
            Belgilangan sana oralig'i uchun davomat ma'lumotlarini yuklab olish
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Sana oralig'i *</Label>
            <DateRangePicker
              from={dateFrom}
              to={dateTo}
              onChange={(f, t) => {
                setDateFrom(f);
                setDateTo(t);
              }}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Sinf</Label>
              <Select
                value={classFilter}
                onValueChange={(v) => setClassFilter(v === "all" ? "" : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Barcha sinflar" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Barcha sinflar</SelectItem>
                  {classList.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Format</Label>
              <Select value={format} onValueChange={setFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="xlsx">Excel (.xlsx)</SelectItem>
                  <SelectItem value="csv">CSV (.csv)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            onClick={handleDownload}
            disabled={loading || !dateFrom || !dateTo}
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            Yuklash
          </Button>
        </CardContent>
      </Card>

      {/* Recent downloads */}
      {reportHistory.length > 0 && (
        <Card className="glass-card border-none premium-shadow">
          <CardHeader className="bg-white/30 dark:bg-slate-900/30 rounded-t-xl backdrop-blur-md border-b border-border/50 pb-4 mb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-primary" />
                So'nggi hisobotlar
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  clearReportHistory();
                }}
              >
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Tozalash
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {reportHistory.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-xl border border-border/50 bg-white/40 dark:bg-slate-950/40 p-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div>
                    <p className="text-sm font-medium">{item.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.dateFrom} — {item.dateTo} · {item.format.toUpperCase()}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.downloadedAt).toLocaleString("uz")}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
