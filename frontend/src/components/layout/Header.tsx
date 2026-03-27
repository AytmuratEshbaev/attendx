import { useNavigate } from "react-router-dom";
import { Sun, Moon, LogOut, User as UserIcon, Menu } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/uiStore";
import { authApi } from "@/services/authApi";
import { NotificationCenter } from "@/components/common/NotificationCenter";

const roleLabels: Record<string, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  teacher: "O'qituvchi",
};

const roleColors: Record<string, string> = {
  super_admin: "bg-primary/10 text-primary border-primary/20",
  admin: "bg-success/10 text-success border-success/20",
  teacher: "bg-accent text-accent-foreground border-accent-foreground/20",
};

export function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { toggleTheme, theme, setSidebarOpen } = useUIStore();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout errors
    }
    logout();
    toast.success("Tizimdan chiqdingiz");
    navigate("/login");
  };

  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : "??";

  return (
    <header className="glass-nav flex h-16 items-center justify-between px-4 sticky top-0 z-40">
      {/* Left: mobile menu */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Right: controls */}
      <div className="flex items-center gap-1">
        <NotificationCenter />

        <Separator orientation="vertical" className="h-5 mx-1" />

        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="rounded-lg text-muted-foreground hover:text-foreground"
          title={theme === "light" ? "Tungi rejim" : "Kunduzgi rejim"}
        >
          {theme === "light" ? (
            <Moon className="h-[18px] w-[18px]" />
          ) : (
            <Sun className="h-[18px] w-[18px]" />
          )}
        </Button>

        <Separator orientation="vertical" className="h-5 mx-1" />

        {/* User dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="gap-2.5 px-2 rounded-lg hover:bg-muted"
            >
              <Avatar className="h-8 w-8 ring-2 ring-primary/20">
                <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="hidden text-left md:block">
                <p className="text-sm font-semibold leading-none text-foreground">
                  {user?.username}
                </p>
                <p
                  className={`mt-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full border inline-block ${
                    roleColors[user?.role ?? ""] ?? "bg-muted text-muted-foreground"
                  }`}
                >
                  {roleLabels[user?.role ?? ""] ?? user?.role}
                </p>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="pb-2">
              <p className="font-semibold">{user?.username}</p>
              <p className="text-xs font-normal text-muted-foreground truncate">
                {user?.email ?? ""}
              </p>
              {user?.role && (
                <Badge variant="secondary" className="mt-1.5 text-[10px]">
                  {roleLabels[user.role] ?? user.role}
                </Badge>
              )}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/settings")}>
              <UserIcon className="mr-2 h-4 w-4" />
              Profil sozlamalari
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="text-destructive focus:text-destructive focus:bg-destructive/10"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Chiqish
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
