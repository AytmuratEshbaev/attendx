import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

/**
 * Global keyboard shortcuts for the dashboard.
 *
 * Alt+1..9 → navigate to routes
 * Alt+S    → focus search (if available on current page)
 */
export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    const ROUTES: Record<string, string> = {
      "1": "/",
      "2": "/students",
      "3": "/attendance",
      "4": "/reports",
      "5": "/devices",
      "6": "/timetables",
      "7": "/access-groups",
      "8": "/webhooks",
      "9": "/users",
      "0": "/settings",
    };

    function handleKeyDown(e: KeyboardEvent) {
      // Skip if user is typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      if (e.altKey && ROUTES[e.key]) {
        e.preventDefault();
        navigate(ROUTES[e.key]);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigate]);
}
