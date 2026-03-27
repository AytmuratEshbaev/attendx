import { useState } from "react";
import { ChevronDown, ChevronUp, X, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DateRangePicker } from "@/components/common/DateRangePicker";
import type { AttendanceFilters } from "@/types";

interface FilterPanelProps {
  filters: AttendanceFilters;
  onChange: (filters: AttendanceFilters) => void;
  classes?: string[];
  devices?: string[];
}

const EMPTY_FILTERS: AttendanceFilters = {
  class_name: "",
  date_from: "",
  date_to: "",
  event_type: "",
  device_name: "",
};

function countActive(filters: AttendanceFilters): number {
  return Object.values(filters).filter((v) => v !== "").length;
}

export function FilterPanel({
  filters,
  onChange,
  classes = [],
  devices = [],
}: FilterPanelProps) {
  const [open, setOpen] = useState(false);
  const activeCount = countActive(filters);

  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            className="gap-2 px-2"
            onClick={() => setOpen((v) => !v)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filtrlar
            {activeCount > 0 && (
              <Badge variant="secondary" className="h-5 text-xs">
                {activeCount}
              </Badge>
            )}
            {open ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
          {activeCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="gap-1 text-muted-foreground hover:text-foreground"
              onClick={() => onChange(EMPTY_FILTERS)}
            >
              <X className="h-3.5 w-3.5" />
              Tozalash
            </Button>
          )}
        </div>

        {open && (
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
            <DateRangePicker
              from={filters.date_from}
              to={filters.date_to}
              onChange={(from, to) =>
                onChange({ ...filters, date_from: from, date_to: to })
              }
            />

            <Select
              value={filters.class_name || "all"}
              onValueChange={(v) =>
                onChange({ ...filters, class_name: v === "all" ? "" : v })
              }
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Barcha sinflar" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha sinflar</SelectItem>
                {classes.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.event_type || "all"}
              onValueChange={(v) =>
                onChange({ ...filters, event_type: v === "all" ? "" : v })
              }
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Barcha turlar" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha turlar</SelectItem>
                <SelectItem value="entry">Kirdi</SelectItem>
                <SelectItem value="exit">Chiqdi</SelectItem>
              </SelectContent>
            </Select>

            {devices.length > 0 && (
              <Select
                value={filters.device_name || "all"}
                onValueChange={(v) =>
                  onChange({
                    ...filters,
                    device_name: v === "all" ? "" : v,
                  })
                }
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Barcha qurilmalar" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Barcha qurilmalar</SelectItem>
                  {devices.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
