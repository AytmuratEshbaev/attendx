import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  sidebarOpen: boolean;
  theme: "light" | "dark";
  pageTitle: string | null;
  notifOpen: boolean;
  lastSeenEventId: string | null;
  studentsView: "table" | "card";
  attendanceView: "table" | "calendar";
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;
  setPageTitle: (title: string | null) => void;
  setNotifOpen: (open: boolean) => void;
  setLastSeenEventId: (id: string | null) => void;
  setStudentsView: (view: "table" | "card") => void;
  setAttendanceView: (view: "table" | "calendar") => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      sidebarOpen: true,
      theme: "light",
      pageTitle: null,
      notifOpen: false,
      lastSeenEventId: null,
      studentsView: "table",
      attendanceView: "table",
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => {
        document.documentElement.classList.toggle("dark", theme === "dark");
        set({ theme });
      },
      toggleTheme: () => {
        const next = get().theme === "light" ? "dark" : "light";
        document.documentElement.classList.toggle("dark", next === "dark");
        set({ theme: next });
      },
      setPageTitle: (title) => set({ pageTitle: title }),
      setNotifOpen: (open) => set({ notifOpen: open }),
      setLastSeenEventId: (id) => set({ lastSeenEventId: id }),
      setStudentsView: (view) => set({ studentsView: view }),
      setAttendanceView: (view) => set({ attendanceView: view }),
    }),
    {
      name: "attendx-ui",
      partialize: (state) => ({
        theme: state.theme,
        studentsView: state.studentsView,
        attendanceView: state.attendanceView,
        lastSeenEventId: state.lastSeenEventId,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.theme === "dark") {
          document.documentElement.classList.add("dark");
        }
      },
    },
  ),
);
