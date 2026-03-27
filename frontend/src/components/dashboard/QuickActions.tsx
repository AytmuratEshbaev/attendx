import { useNavigate } from "react-router-dom";
import {
  UserPlus,
  CalendarCheck,
  FileText,
  Monitor,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACTIONS = [
  {
    icon: UserPlus,
    label: "Yangi o'quvchi",
    description: "O'quvchi qo'shish",
    path: "/students",
  },
  {
    icon: CalendarCheck,
    label: "Davomat",
    description: "Davomat ko'rish",
    path: "/attendance",
  },
  {
    icon: FileText,
    label: "Hisobotlar",
    description: "Hisobot olish",
    path: "/reports",
  },
  {
    icon: Monitor,
    label: "Qurilmalar",
    description: "Qurilma holati",
    path: "/devices",
  },
];

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Tezkor harakatlar</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {ACTIONS.map(({ icon: Icon, label, description, path }) => (
            <Button
              key={path + label}
              variant="outline"
              className="flex h-auto flex-col items-center gap-2 py-4"
              onClick={() => navigate(path)}
            >
              <Icon className="h-5 w-5 text-primary" />
              <div className="text-center">
                <p className="text-sm font-medium">{label}</p>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
