import { useNavigate } from "react-router-dom";
import { Trash2, ScanFace, CreditCard, Fingerprint, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import type { Student } from "@/types";
import { cn } from "@/lib/utils";

interface StudentCardProps {
  student: Student;
  isAdmin?: boolean;
  onDelete?: (id: string) => void;
}

// Auth-aware face image loader (Bearer token bilan)
function StudentFaceImage({
  studentId,
  name,
  className,
}: {
  studentId: string;
  name: string;
  className?: string;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);
  const prevSrc = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(false);
    setSrc(null);

    fetch(`/api/v1/students/${studentId}/face`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error("not found");
        return r.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        prevSrc.current = url;
        setSrc(url);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });

    return () => {
      cancelled = true;
      if (prevSrc.current) {
        URL.revokeObjectURL(prevSrc.current);
        prevSrc.current = null;
      }
    };
  }, [studentId, accessToken]);

  const initials = name
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (src && !error) {
    return (
      <img
        src={src}
        alt={name}
        className={cn("h-full w-full object-cover", className)}
      />
    );
  }

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-gradient-to-br from-primary/10 to-primary/5">
      <span className="text-3xl font-bold tracking-tight text-primary/60">
        {initials}
      </span>
    </div>
  );
}

export function StudentCard({ student, isAdmin, onDelete }: StudentCardProps) {
  const navigate = useNavigate();
  const groupName = student.category?.name ?? student.class_name ?? null;

  return (
    <div
      className={cn(
        "group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-border/60 bg-card shadow-sm",
        "transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md",
      )}
      onClick={() => navigate(`/students/${student.id}`)}
    >
      {/* ── Photo ────────────────────────────────────── */}
      <div className="relative aspect-square w-full overflow-hidden bg-muted">
        <StudentFaceImage studentId={student.id} name={student.name} />

        {/* Gradient overlay — bottom fade for readability */}
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/40 to-transparent" />

        {/* Active status pill — top-left */}
        <div className="absolute left-2.5 top-2.5">
          {student.is_active ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white backdrop-blur-sm">
              <CheckCircle2 className="h-2.5 w-2.5" />
              Faol
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-500/90 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white backdrop-blur-sm">
              <XCircle className="h-2.5 w-2.5" />
              Faol emas
            </span>
          )}
        </div>

        {/* Delete button — top-right (admin only) */}
        {isAdmin && onDelete && (
          <Button
            variant="destructive"
            size="icon"
            className="absolute right-2 top-2 h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(student.id);
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        )}

        {/* Credential icons — bottom-right overlay */}
        <div className="absolute bottom-2 right-2.5 flex items-center gap-1.5">
          <div
            title="Yuz"
            className={cn(
              "rounded-full p-0.5",
              student.face_registered
                ? "text-white drop-shadow"
                : "text-white/30",
            )}
          >
            <ScanFace className="h-4 w-4" />
          </div>
          <div title="Karta" className="rounded-full p-0.5 text-white/30">
            <CreditCard className="h-4 w-4" />
          </div>
          <div title="Barmoq izi" className="rounded-full p-0.5 text-white/30">
            <Fingerprint className="h-4 w-4" />
          </div>
        </div>
      </div>

      {/* ── Info ─────────────────────────────────────── */}
      <div className="flex flex-col gap-0.5 px-3 py-2.5">
        <p className="truncate text-sm font-semibold leading-snug text-foreground">
          {student.name}
        </p>
        <div className="flex items-center justify-between gap-1">
          <span className="font-mono text-[11px] text-muted-foreground">
            #{student.employee_no}
          </span>
          {groupName && (
            <span className="truncate rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              {groupName}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
