import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, ScanFace, Upload, Loader2, CalendarDays, UserCog, Camera } from "lucide-react";
import { useRef, useState } from "react";
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

  // Attendance stats computed from history
  const totalRecords = history.length;
  const entryCount = history.filter((r) => r.event_type === "entry").length;
  const exitCount = history.filter((r) => r.event_type === "exit").length;
  const presentDays = attendanceStats?.present_days ?? 0;
  const attendancePct = attendanceStats?.percentage ?? 0;

  // Last 30 days chart data
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
          <TabsTrigger value="info" className="gap-1.5">
            <UserCog className="h-4 w-4" />
            Ma'lumot
          </TabsTrigger>
          <TabsTrigger value="face" className="gap-1.5">
            <Camera className="h-4 w-4" />
            Yuz boshqaruvi
          </TabsTrigger>
        </TabsList>

        {/* Attendance tab */}
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

          {/* Stats summary */}
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

          {/* Mini bar chart */}
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

          {/* Attendance history table */}
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

        {/* Info tab */}
        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Ma'lumot</CardTitle>
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
        </TabsContent>

        {/* Face Management tab */}
        <TabsContent value="face">
          <Card>
            <CardHeader>
              <CardTitle>Yuz rasmi</CardTitle>
              <CardDescription>Yuz tanish uchun rasm yuklang</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <div className="flex h-32 w-32 items-center justify-center rounded-full border-2 border-dashed">
                {student.face_registered ? (
                  <ScanFace className="h-16 w-16 text-primary" />
                ) : (
                  <ScanFace className="h-16 w-16 text-muted-foreground" />
                )}
              </div>
              <StatusBadge
                status={student.face_registered ? "active" : "inactive"}
                label={student.face_registered ? "Ro'yxatdan o'tgan" : "Ro'yxatdan o'tmagan"}
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
                onClick={() => fileInputRef.current?.click()}
                disabled={faceMutation.isPending}
              >
                {faceMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="mr-2 h-4 w-4" />
                )}
                Rasm yuklash
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
