import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  ScanFace,
  Upload,
  Loader2,
  CalendarDays,
  UserCog,
  CreditCard,
  Fingerprint,
  Camera,
} from "lucide-react";
import { useRef, useState, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { studentsApi } from "@/services/studentsApi";
import { getErrorMessage } from "@/services/api";
import { useStudent } from "@/hooks/useStudents";
import { useStudentAttendance } from "@/hooks/useAttendance";
import { DateRangePicker } from "@/components/common/DateRangePicker";
import { StatusBadge } from "@/components/common/StatusBadge";
import type { StudentUpdate } from "@/types";

// ─── Yuz fotosi (auth bilan) ─────────────────────────────────────────────────
function StudentFacePhoto({ studentId, hasPhoto }: { studentId: string; hasPhoto: boolean }) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!hasPhoto) return;
    let cancelled = false;
    let blobUrl: string | null = null;

    fetch(`/api/v1/students/${studentId}/face`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => { if (!r.ok) throw new Error(); return r.blob(); })
      .then((blob) => {
        if (cancelled) return;
        blobUrl = URL.createObjectURL(blob);
        setSrc(blobUrl);
      })
      .catch(() => { if (!cancelled) setError(true); });

    return () => {
      cancelled = true;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [studentId, hasPhoto, accessToken]);

  if (hasPhoto && src && !error) {
    return (
      <img
        src={src}
        alt="Yuz fotosi"
        className="h-40 w-40 rounded-lg object-cover border"
      />
    );
  }
  return (
    <div className="flex h-40 w-40 items-center justify-center rounded-lg border-2 border-dashed bg-muted/30">
      <ScanFace className="h-16 w-16 text-muted-foreground/40" />
    </div>
  );
}

// ─── So'nggi kirish rasmi (capture image proxy) ─────────────────────────────
function LastEntryImage({
  pictureUrl,
  eventTime,
  deviceName,
}: {
  pictureUrl: string;
  eventTime: string;
  deviceName: string | null;
}) {
  const [failed, setFailed] = useState(false);
  const encoded = btoa(pictureUrl);
  const src = `/api/v1/attendance/capture-image?url=${encodeURIComponent(encoded)}`;

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">So'nggi yuz orqali kirish rasmi</p>
      <div className="flex items-start gap-4">
        {!failed ? (
          <img
            src={src}
            alt="Kirish rasmi"
            className="h-28 w-20 rounded-md object-cover border"
            onError={() => setFailed(true)}
          />
        ) : (
          <div className="flex h-28 w-20 items-center justify-center rounded-md border-2 border-dashed bg-muted/30">
            <Camera className="h-8 w-8 text-muted-foreground/40" />
          </div>
        )}
        <div className="space-y-1 text-sm text-muted-foreground">
          <p>
            {new Date(
              eventTime.endsWith("Z") || eventTime.includes("+")
                ? eventTime
                : eventTime + "Z",
            ).toLocaleString("uz")}
          </p>
          {deviceName && <p>Qurilma: {deviceName}</p>}
        </div>
      </div>
    </div>
  );
}

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState("attendance");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { data: studentRes, isLoading } = useStudent(id);
  const { data: historyRes } = useStudentAttendance(id, {
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const student = studentRes?.data?.data;
  const historyData = historyRes?.data?.data;
  const history = historyData?.records ?? [];
  const attendanceStats = historyData?.stats;

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<StudentUpdate>({});

  const updateMutation = useMutation({
    mutationFn: (data: StudentUpdate) => studentsApi.update(id!, data),
    onSuccess: () => {
      toast.success("O'quvchi yangilandi");
      setEditing(false);
      queryClient.invalidateQueries({ queryKey: ["student", id] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const faceMutation = useMutation({
    mutationFn: (file: File) => studentsApi.uploadFace(id!, file),
    onSuccess: () => {
      toast.success("Yuz rasmi yuklandi");
      queryClient.invalidateQueries({ queryKey: ["student", id] });
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const startEditing = () => {
    if (student) {
      setForm({
        name: student.name ?? undefined,
        class_name: student.class_name ?? undefined,
        parent_phone: student.parent_phone ?? "",
      });
      setEditing(true);
    }
  };

  // Stats
  const totalRecords = history.length;
  const entryCount = history.filter((r) => r.event_type === "entry").length;
  const exitCount = history.filter((r) => r.event_type === "exit").length;
  const presentDays = attendanceStats?.present_days ?? 0;
  const attendancePct = attendanceStats?.percentage ?? 0;

  // Chart data
  const chartData = (() => {
    const dayMap: Record<string, { date: string; entry: number; exit: number }> = {};
    history.forEach((r) => {
      const day = r.event_time.split("T")[0];
      if (!dayMap[day]) dayMap[day] = { date: day, entry: 0, exit: 0 };
      if (r.event_type === "entry") dayMap[day].entry++;
      else dayMap[day].exit++;
    });
    return Object.values(dayMap).sort((a, b) => a.date.localeCompare(b.date)).slice(-30);
  })();

  // So'nggi yuz orqali kirish rasmi
  const lastFaceEntry = history.find(
    (r) => r.verify_mode?.toLowerCase().includes("face") && r.picture_url,
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!student) {
    return <div className="text-muted-foreground">O'quvchi topilmadi</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/students")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{student.name}</h1>
          <p className="text-muted-foreground">
            {student.class_name} &bull; {student.employee_no}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={student.is_active ? "active" : "inactive"} />
          {student.face_registered && (
            <Badge variant="outline" className="gap-1">
              <ScanFace className="h-3 w-3" /> Yuz
            </Badge>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="attendance" className="gap-1.5">
            <CalendarDays className="h-4 w-4" />
            Davomat
          </TabsTrigger>
          <TabsTrigger value="profile" className="gap-1.5">
            <UserCog className="h-4 w-4" />
            Ma'lumot va Boshqaruv
          </TabsTrigger>
        </TabsList>

        {/* ── Davomat tab ── */}
        <TabsContent value="attendance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sana oralig'i</CardTitle>
            </CardHeader>
            <CardContent>
              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={(f, t) => {
                  setDateFrom(f);
                  setDateTo(t);
                }}
              />
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-2xl font-bold">{totalRecords}</p>
                <p className="text-sm text-muted-foreground">Jami yozuvlar</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-2xl font-bold text-green-600">{entryCount}</p>
                <p className="text-sm text-muted-foreground">Kirdi</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-2xl font-bold text-orange-500">{exitCount}</p>
                <p className="text-sm text-muted-foreground">Chiqdi</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-2xl font-bold text-blue-600">{attendancePct}%</p>
                <p className="text-sm text-muted-foreground">{presentDays} kun keldi</p>
              </CardContent>
            </Card>
          </div>

          {chartData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Davomat grafigi</CardTitle>
                <CardDescription>Kunlik kirish va chiqishlar</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" />
                    <Tooltip />
                    <Bar dataKey="entry" name="Kirdi" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="exit" name="Chiqdi" fill="hsl(var(--muted-foreground))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Davomat tarixi</CardTitle>
              <CardDescription>{totalRecords} ta yozuv</CardDescription>
            </CardHeader>
            <CardContent>
              {history.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Sana va vaqt</TableHead>
                        <TableHead>Turi</TableHead>
                        <TableHead>Qurilma</TableHead>
                        <TableHead>Usul</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {history.map((record) => (
                        <TableRow key={record.id}>
                          <TableCell>
                            {new Date(record.event_time).toLocaleString("uz")}
                          </TableCell>
                          <TableCell>
                            <StatusBadge
                              status={record.event_type === "entry" ? "entry" : "exit"}
                            />
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {record.device_name ?? "Noma'lum"}
                          </TableCell>
                          <TableCell className="text-muted-foreground text-xs">
                            {record.verify_mode === "face" || record.verify_mode?.includes("face")
                              ? "Yuz orqali"
                              : record.verify_mode === "card" || record.verify_mode?.includes("card")
                              ? "Karta"
                              : record.verify_mode?.includes("finger")
                              ? "Barmoq izi"
                              : record.verify_mode ?? "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="py-8 text-center text-muted-foreground">
                  Davomat yozuvlari topilmadi
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── Ma'lumot va Boshqaruv tab ── */}
        <TabsContent value="profile" className="space-y-4">
          {/* Shaxsiy ma'lumot */}
          <Card>
            <CardHeader>
              <CardTitle>Shaxsiy ma'lumot</CardTitle>
              <div className="flex gap-2">
                {!editing ? (
                  <Button size="sm" onClick={startEditing}>Tahrirlash</Button>
                ) : (
                  <>
                    <Button variant="outline" size="sm" onClick={() => setEditing(false)}>
                      Bekor qilish
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => updateMutation.mutate(form)}
                      disabled={updateMutation.isPending}
                    >
                      {updateMutation.isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Saqlash
                    </Button>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {editing ? (
                <>
                  <div className="space-y-2">
                    <Label>Ismi</Label>
                    <Input
                      value={form.name ?? ""}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Sinf</Label>
                    <Input
                      value={form.class_name ?? ""}
                      onChange={(e) => setForm({ ...form, class_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Ota-ona telefoni</Label>
                    <Input
                      value={form.parent_phone ?? ""}
                      onChange={(e) => setForm({ ...form, parent_phone: e.target.value })}
                    />
                  </div>
                </>
              ) : (
                <dl className="space-y-3">
                  {([
                    ["Tashqi ID", student.external_id],
                    ["Xodim raqami", student.employee_no],
                    ["Ota-ona telefoni", student.parent_phone],
                    ["Yaratilgan", new Date(student.created_at).toLocaleDateString("uz")],
                  ] as [string, string | null][]).map(([label, value]) => (
                    <div key={label} className="flex justify-between">
                      <dt className="text-sm text-muted-foreground">{label}</dt>
                      <dd className="text-sm font-medium">{value || "—"}</dd>
                    </div>
                  ))}
                  <div className="flex justify-between">
                    <dt className="text-sm text-muted-foreground">Holat</dt>
                    <dd>
                      <StatusBadge status={student.is_active ? "active" : "inactive"} />
                    </dd>
                  </div>
                </dl>
              )}
            </CardContent>
          </Card>

          {/* Kirish usullari va yuz boshqaruvi */}
          <Card>
            <CardHeader>
              <CardTitle>Kirish usullari</CardTitle>
              <CardDescription>
                Ro'yxatdan o'tgan usullar va yuz fotosini boshqarish
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Usul indikatorlari */}
              <div className="grid grid-cols-3 gap-3">
                {/* Yuz */}
                <div
                  className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors ${
                    student.face_registered
                      ? "border-primary/40 bg-primary/5"
                      : "border-border bg-muted/20 opacity-50"
                  }`}
                >
                  <ScanFace
                    className={`h-8 w-8 ${student.face_registered ? "text-primary" : "text-muted-foreground"}`}
                  />
                  <span className="text-xs font-medium">Yuz</span>
                  <Badge
                    variant={student.face_registered ? "default" : "outline"}
                    className="text-xs"
                  >
                    {student.face_registered ? "Faol" : "Yo'q"}
                  </Badge>
                </div>

                {/* Karta */}
                <div className="flex flex-col items-center gap-2 rounded-lg border border-border bg-muted/20 p-4 opacity-40">
                  <CreditCard className="h-8 w-8 text-muted-foreground" />
                  <span className="text-xs font-medium">Karta</span>
                  <Badge variant="outline" className="text-xs">
                    Yo'q
                  </Badge>
                </div>

                {/* Barmoq izi */}
                <div className="flex flex-col items-center gap-2 rounded-lg border border-border bg-muted/20 p-4 opacity-40">
                  <Fingerprint className="h-8 w-8 text-muted-foreground" />
                  <span className="text-xs font-medium">Barmoq izi</span>
                  <Badge variant="outline" className="text-xs">
                    Yo'q
                  </Badge>
                </div>
              </div>

              {/* Yuz fotosi */}
              <div className="space-y-3">
                <p className="text-sm font-medium">Yuz rasmi</p>
                <div className="flex items-start gap-4">
                  <StudentFacePhoto studentId={student.id} hasPhoto={student.face_registered} />
                  <div className="space-y-2">
                    <StatusBadge
                      status={student.face_registered ? "active" : "inactive"}
                      label={
                        student.face_registered
                          ? "Ro'yxatdan o'tgan"
                          : "Ro'yxatdan o'tmagan"
                      }
                    />
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) faceMutation.mutate(file);
                      }}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={faceMutation.isPending}
                    >
                      {faceMutation.isPending ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Upload className="mr-2 h-4 w-4" />
                      )}
                      {student.face_registered ? "Yangilash" : "Rasm yuklash"}
                    </Button>
                  </div>
                </div>
              </div>

              {/* So'nggi yuz orqali kirish rasmi */}
              {lastFaceEntry?.picture_url && (
                <div className="border-t pt-4">
                  <LastEntryImage
                    pictureUrl={lastFaceEntry.picture_url}
                    eventTime={lastFaceEntry.event_time}
                    deviceName={lastFaceEntry.device_name ?? null}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
