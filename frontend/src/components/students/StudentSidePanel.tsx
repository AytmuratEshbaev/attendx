import { useNavigate } from "react-router-dom";
import { ExternalLink, Phone } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useStudent } from "@/hooks/useStudents";
import { useStudentAttendance } from "@/hooks/useAttendance";

interface StudentSidePanelProps {
  studentId: string | null;
  onClose: () => void;
}

export function StudentSidePanel({ studentId, onClose }: StudentSidePanelProps) {
  const navigate = useNavigate();
  const { data: studentRes, isLoading } = useStudent(studentId ?? undefined);
  const { data: attendanceRes } = useStudentAttendance(studentId ?? undefined);

  const student = studentRes?.data?.data;
  const attendanceData = attendanceRes?.data?.data;
  const recentRecords = attendanceData?.records?.slice(0, 20) ?? [];
  const stats = attendanceData?.stats;

  const initials = student?.name
    ? student.name
        .split(" ")
        .map((w: string) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "??";

  return (
    <Sheet open={studentId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="w-80 sm:w-96 flex flex-col">
        <SheetHeader>
          <SheetTitle>O'quvchi ma'lumotlari</SheetTitle>
        </SheetHeader>

        <div className="mt-4 flex-1 overflow-y-auto space-y-4">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-48 w-full" />
            </div>
          ) : student ? (
            <>
              {/* Profile */}
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-primary/10 text-sm font-medium text-primary">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold">{student.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {student.category?.name ?? student.class_name ?? "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    #{student.employee_no}
                  </p>
                </div>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-1.5">
                <Badge variant={student.is_active ? "default" : "destructive"} className="text-xs">
                  {student.is_active ? "Faol" : "Faol emas"}
                </Badge>
                {student.face_registered && (
                  <Badge variant="secondary" className="text-xs">Yuz ro'yxatdan o'tgan</Badge>
                )}
              </div>

              {/* Phone */}
              {student.parent_phone && (
                <div className="space-y-1 rounded-md border p-3 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Phone className="h-3.5 w-3.5" />
                    {student.parent_phone}
                  </div>
                </div>
              )}

              {/* Mini stats */}
              {stats && (
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-md border p-2">
                    <p className="text-lg font-bold">{stats.total_days}</p>
                    <p className="text-xs text-muted-foreground">Jami</p>
                  </div>
                  <div className="rounded-md border p-2">
                    <p className="text-lg font-bold text-green-600">{stats.present_days}</p>
                    <p className="text-xs text-muted-foreground">Keldi</p>
                  </div>
                  <div className="rounded-md border p-2">
                    <p className="text-lg font-bold text-primary">{stats.percentage}%</p>
                    <p className="text-xs text-muted-foreground">Davomat</p>
                  </div>
                </div>
              )}

              {/* Recent records */}
              {recentRecords.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium">So'nggi hodisalar</p>
                  <div className="space-y-1.5">
                    {recentRecords.map((r) => (
                      <div
                        key={r.id}
                        className="flex items-center justify-between rounded-md border px-3 py-2 text-xs"
                      >
                        <span className="text-muted-foreground">
                          {new Date(r.event_time).toLocaleString("uz", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        <Badge
                          variant={r.event_type === "entry" ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {r.event_type === "entry" ? "Kirdi" : "Chiqdi"}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Full profile button */}
              <Button
                className="w-full gap-2"
                variant="outline"
                onClick={() => {
                  onClose();
                  navigate(`/students/${student.id}`);
                }}
              >
                <ExternalLink className="h-4 w-4" />
                To'liq profil
              </Button>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-muted-foreground">
              O'quvchi topilmadi
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
