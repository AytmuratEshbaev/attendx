import { useNavigate } from "react-router-dom";
import { Trash2, ScanFace, Phone } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { Student } from "@/types";

interface StudentCardProps {
  student: Student;
  isAdmin?: boolean;
  onDelete?: (id: string) => void;
}

export function StudentCard({ student, isAdmin, onDelete }: StudentCardProps) {
  const navigate = useNavigate();

  const initials = student.name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <Card
      className="cursor-pointer glass-card border-none hover:border-primary/20 premium-shadow group"
      onClick={() => navigate(`/students/${student.id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 ring-2 ring-primary/10 group-hover:ring-primary/30 transition-all shadow-sm">
              <AvatarFallback className="bg-gradient-premium text-sm font-bold text-white">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-medium leading-tight">{student.name}</p>
              <p className="text-xs text-muted-foreground">
                {student.category?.name ?? student.class_name ?? "—"}
              </p>
              <p className="text-xs text-muted-foreground">
                #{student.employee_no}
              </p>
            </div>
          </div>
          {isAdmin && onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(student.id);
              }}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          <Badge
            variant={student.is_active ? "default" : "destructive"}
            className="text-xs"
          >
            {student.is_active ? "Faol" : "Faol emas"}
          </Badge>
          {student.face_registered && (
            <Badge variant="secondary" className="gap-1 text-xs">
              <ScanFace className="h-3 w-3" />
              Yuz
            </Badge>
          )}
          {student.parent_phone && (
            <Badge variant="outline" className="gap-1 text-xs">
              <Phone className="h-3 w-3" />
              {student.parent_phone}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
