import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusType = "online" | "offline" | "active" | "inactive" | "entry" | "exit";

const STATUS_CONFIG: Record<StatusType, { label: string; dotColor: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  online: { label: "Onlayn", dotColor: "bg-green-500", variant: "default" },
  offline: { label: "Oflayn", dotColor: "bg-red-400", variant: "destructive" },
  active: { label: "Faol", dotColor: "bg-green-500", variant: "default" },
  inactive: { label: "Faol emas", dotColor: "bg-red-400", variant: "destructive" },
  entry: { label: "Kirdi", dotColor: "bg-green-500", variant: "default" },
  exit: { label: "Chiqdi", dotColor: "bg-orange-400", variant: "secondary" },
};

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <Badge variant={config.variant} className={cn("gap-1.5", className)}>
      <span className={cn("h-2 w-2 rounded-full", config.dotColor)} />
      {label ?? config.label}
    </Badge>
  );
}
