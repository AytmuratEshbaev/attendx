import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/store/authStore";
import type { AttendanceRecord } from "@/types";

interface SSEEvent extends Partial<AttendanceRecord> {
  student_id: string;
  student_name: string;
  class_name: string;
  device_name: string;
  event_type: "entry" | "exit";
  event_time: string;
  verify_mode?: string;
  picture_url?: string | null;
}

interface UseSSEAttendanceOptions {
  classFilter?: string;
  maxEvents?: number;
  enabled?: boolean;
}

interface UseSSEAttendanceReturn {
  events: SSEEvent[];
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

/**
 * Subscribe to real-time attendance events via Server-Sent Events.
 * Falls back gracefully if SSE is unavailable.
 */
export function useSSEAttendance({
  classFilter,
  maxEvents = 50,
  enabled = true,
}: UseSSEAttendanceOptions = {}): UseSSEAttendanceReturn {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const reconnectAttemptRef = useRef(0);

  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current) return;

    // Close existing connection
    esRef.current?.close();

    const token = useAuthStore.getState().accessToken;
    if (!token) return;

    // Build URL with auth token as query param (SSE doesn't support custom headers)
    const params = new URLSearchParams({ token });
    if (classFilter) params.set("class_name", classFilter);

    // Use the SSE endpoint
    const url = `/api/v1/sse/attendance?${params}`;

    try {
      const es = new EventSource(url);
      esRef.current = es;

      es.addEventListener("connected", () => {
        if (mountedRef.current) {
          setIsConnected(true);
          setError(null);
          reconnectAttemptRef.current = 0;
        }
      });

      es.addEventListener("attendance", (e: MessageEvent) => {
        if (!mountedRef.current) return;
        try {
          const data: SSEEvent = JSON.parse(e.data);
          setEvents((prev) => {
            const next = [data, ...prev];
            return next.slice(0, maxEvents);
          });
        } catch {
          // ignore parse errors
        }
      });

      es.onerror = () => {
        if (!mountedRef.current) return;
        setIsConnected(false);
        esRef.current?.close();

        // Exponential backoff: 5s, 10s, 20s, 40s, max 60s
        const attempt = reconnectAttemptRef.current;
        const delay = Math.min(5000 * Math.pow(2, attempt), 60000);
        reconnectAttemptRef.current = attempt + 1;

        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, delay);
      };
    } catch (err) {
      setError("SSE ulash muvaffaqiyatsiz");
    }
  }, [classFilter, enabled, maxEvents]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      esRef.current?.close();
    };
  }, [connect]);

  const reconnect = useCallback(() => {
    setError(null);
    reconnectAttemptRef.current = 0;
    connect();
  }, [connect]);

  return { events, isConnected, error, reconnect };
}
