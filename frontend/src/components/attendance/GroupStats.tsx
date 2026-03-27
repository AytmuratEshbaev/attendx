import { useAttendanceStats } from "@/hooks/useAttendance";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

function getPctColor(pct: number): string {
  if (pct >= 90) return "#22c55e";
  if (pct >= 70) return "#eab308";
  if (pct >= 50) return "#f97316";
  return "#ef4444";
}

function getPctBadgeVariant(pct: number): "default" | "secondary" | "outline" | "destructive" {
  if (pct >= 70) return "default";
  if (pct >= 50) return "secondary";
  return "destructive";
}

export function GroupStats() {
  const { data: statsRes, isLoading } = useAttendanceStats();
  const stats = statsRes?.data?.data;

  const chartData = Object.entries(stats?.by_class ?? {})
    .map(([name, d]) => ({
      name,
      percentage: Math.round(d.percentage),
      present: d.present,
      total: d.total,
    }))
    .sort((a, b) => b.percentage - a.percentage);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Sinf bo'yicha taqqoslash</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Ma'lumot mavjud emas
          </div>
        ) : (
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={Math.max(120, chartData.length * 36)}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
              >
                <XAxis type="number" domain={[0, 100]} unit="%" className="text-xs" />
                <YAxis dataKey="name" type="category" width={60} className="text-xs" />
                <Tooltip
                  formatter={(value: number) => [`${value}%`, "Davomat"]}
                />
                <Bar dataKey="percentage" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={getPctColor(entry.percentage)}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Table view */}
            <div className="space-y-1">
              {chartData.map((cls) => (
                <div
                  key={cls.name}
                  className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                >
                  <span className="font-medium">{cls.name}</span>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <span>
                      {cls.present}/{cls.total}
                    </span>
                    <Badge
                      variant={getPctBadgeVariant(cls.percentage)}
                      className="w-14 justify-center text-xs"
                    >
                      {cls.percentage}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
