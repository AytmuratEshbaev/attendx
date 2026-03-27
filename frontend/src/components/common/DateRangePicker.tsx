import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface DateRangePickerProps {
  from: string;
  to: string;
  onChange: (from: string, to: string) => void;
}

export function DateRangePicker({ from, to, onChange }: DateRangePickerProps) {
  const today = new Date();
  const fmt = (d: Date) => d.toISOString().split("T")[0];

  const presets = [
    {
      label: "Bugun",
      apply: () => {
        const d = fmt(today);
        onChange(d, d);
      },
    },
    {
      label: "Shu hafta",
      apply: () => {
        const day = today.getDay();
        const diff = day === 0 ? 6 : day - 1;
        const start = new Date(today);
        start.setDate(today.getDate() - diff);
        onChange(fmt(start), fmt(today));
      },
    },
    {
      label: "Shu oy",
      apply: () => {
        const start = new Date(today.getFullYear(), today.getMonth(), 1);
        onChange(fmt(start), fmt(today));
      },
    },
    {
      label: "Oxirgi 30 kun",
      apply: () => {
        const start = new Date(today);
        start.setDate(today.getDate() - 29);
        onChange(fmt(start), fmt(today));
      },
    },
  ];

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div className="flex gap-2">
        <Input
          type="date"
          value={from}
          onChange={(e) => onChange(e.target.value, to)}
          className="w-[150px]"
        />
        <span className="flex items-center text-muted-foreground">—</span>
        <Input
          type="date"
          value={to}
          onChange={(e) => onChange(from, e.target.value)}
          className="w-[150px]"
        />
      </div>
      <div className="flex flex-wrap gap-1">
        {presets.map((preset) => (
          <Button
            key={preset.label}
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={preset.apply}
          >
            {preset.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
