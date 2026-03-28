import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  ClipboardCheck,
  FileBarChart,
  Monitor,
  CalendarDays,
  Shield,
  Webhook,
  UserCog,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  Download,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import darkLogoUrl from "@/assets/dark_logo.webp";
import whiteLogoUrl from "@/assets/white_logo.webp";

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
  roles?: string[];
}

interface NavGroup {
  label: string;
  items: NavItem[];
  adminOnly?: boolean;
}

const navGroups: NavGroup[] = [
  {
    label: "Asosiy",
    items: [
      { to: "/", icon: LayoutDashboard, label: "Bosh sahifa" },
      { to: "/students", icon: Users, label: "O'quvchilar" },
      { to: "/attendance", icon: ClipboardCheck, label: "Davomat" },
      { to: "/reports", icon: FileBarChart, label: "Hisobotlar" },
    ],
  },
  {
    label: "Boshqaruv",
    adminOnly: true,
    items: [
      { to: "/devices", icon: Monitor, label: "Qurilmalar", roles: ["super_admin", "admin"] },
      { to: "/timetables", icon: CalendarDays, label: "Jadvallar", roles: ["super_admin", "admin"] },
      { to: "/access-groups", icon: Shield, label: "Kirish guruhlari", roles: ["super_admin", "admin"] },
      { to: "/analytics", icon: BarChart3, label: "Analitika", roles: ["super_admin", "admin"] },
      { to: "/webhooks", icon: Webhook, label: "Webhooklar", roles: ["super_admin", "admin"] },
      { to: "/import-persons", icon: Download, label: "Import", roles: ["super_admin", "admin"] },
    ],
  },
  {
    label: "Tizim",
    items: [
      { to: "/users", icon: UserCog, label: "Foydalanuvchilar", roles: ["super_admin"] },
      { to: "/settings", icon: Settings, label: "Sozlamalar", roles: ["super_admin", "admin"] },
    ],
  },
];

function NavItemLink({
  item,
  collapsed,
}: {
  item: NavItem;
  collapsed: boolean;
}) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      end={item.to === "/"}
      className={({ isActive }) =>
        cn(
          "sidebar-item",
          isActive && "sidebar-item-active",
          collapsed && "justify-center px-2",
        )
      }
    >
      <Icon className="h-[18px] w-[18px] flex-shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </NavLink>
  );
}

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const { sidebarOpen, toggleSidebar, theme } = useUIStore();

  const logoSrc = theme === "dark" ? darkLogoUrl : whiteLogoUrl;

  const canSee = (item: NavItem) =>
    !item.roles || (user && item.roles.includes(user.role));

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "sidebar-bg flex h-screen flex-col transition-all duration-300 z-50 flex-shrink-0",
          sidebarOpen ? "w-60" : "w-[60px]",
        )}
      >
        {/* Logo area */}
        <div
          className={cn(
            "flex h-16 items-center border-b flex-shrink-0",
            sidebarOpen ? "px-4 gap-3" : "justify-center px-2",
          )}
          style={{ borderColor: "hsl(var(--sidebar-border))" }}
        >
          <div
            className={cn(
              "flex-shrink-0 rounded-xl overflow-hidden",
              sidebarOpen ? "h-9 w-9" : "h-8 w-8",
            )}
          >
            <img
              src={logoSrc}
              alt="AttendX Logo"
              className="w-full h-full object-contain"
            />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <p
                className="text-sm font-bold tracking-tight leading-none"
                style={{ color: "hsl(var(--sidebar-foreground))" }}
              >
                AttendX
              </p>
              <p
                className="text-[10px] mt-0.5 truncate"
                style={{ color: "hsl(var(--sidebar-foreground) / 0.5)" }}
              >
                Smart Attendance System
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navGroups.map((group) => {
            const visibleItems = group.items.filter(canSee);
            if (visibleItems.length === 0) return null;

            return (
              <div key={group.label} className="mb-1">
                {sidebarOpen && (
                  <p className="sidebar-section-label">{group.label}</p>
                )}
                {!sidebarOpen && group.label !== "Asosiy" && (
                  <div
                    className="mx-2 my-2 h-px"
                    style={{ backgroundColor: "hsl(var(--sidebar-border))" }}
                  />
                )}
                <div className="space-y-0.5">
                  {visibleItems.map((item) => {
                    if (!sidebarOpen) {
                      return (
                        <Tooltip key={item.to}>
                          <TooltipTrigger asChild>
                            <NavItemLink item={item} collapsed={true} />
                          </TooltipTrigger>
                          <TooltipContent side="right" className="font-medium">
                            {item.label}
                          </TooltipContent>
                        </Tooltip>
                      );
                    }
                    return (
                      <NavItemLink key={item.to} item={item} collapsed={false} />
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        {/* Collapse toggle */}
        <div
          className="border-t p-2 flex-shrink-0"
          style={{ borderColor: "hsl(var(--sidebar-border))" }}
        >
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "w-full transition-colors",
              "hover:bg-sidebar-hover",
              sidebarOpen ? "justify-start gap-2 px-3" : "justify-center px-2",
            )}
            style={{ color: "hsl(var(--sidebar-foreground) / 0.6)" }}
            onClick={toggleSidebar}
          >
            {sidebarOpen ? (
              <>
                <PanelLeftClose className="h-4 w-4 flex-shrink-0" />
                <span className="text-xs">Yopish</span>
              </>
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
