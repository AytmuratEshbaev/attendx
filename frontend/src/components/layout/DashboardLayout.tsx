import { Outlet } from "react-router-dom";
import { useUIStore } from "@/store/uiStore";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Breadcrumbs } from "@/components/common/Breadcrumbs";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";

export function DashboardLayout() {
  useKeyboardShortcuts();
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Desktop sidebar */}
      {!isMobile && <Sidebar />}

      {/* Mobile sidebar as sheet */}
      {isMobile && (
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetContent side="left" className="w-60 p-0 border-0">
            <Sidebar />
          </SheetContent>
        </Sheet>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Header />
        <Breadcrumbs />
        <main className="flex flex-col flex-1 min-h-0 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
        <footer className="border-t border-border/60 px-4 py-2.5 text-center text-xs text-muted-foreground bg-card/60 backdrop-blur-sm">
          Muhammad al-Xorazmiy nomidagi IT maktabi Nukus filiali &bull; Barcha huquqlar himoyalangan &copy; 2026
        </footer>
      </div>
    </div>
  );
}
