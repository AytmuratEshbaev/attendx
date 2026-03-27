import { useState, useCallback, useEffect } from "react";

export interface ReportHistoryItem {
    name: string;
    dateFrom: string;
    dateTo: string;
    format: string;
    downloadedAt: string;
}

const HISTORY_KEY = "attendx-report-history";

export function useReportHistory() {
    const [reportHistory, setReportHistory] = useState<ReportHistoryItem[]>([]);

    // Load history on mount
    useEffect(() => {
        try {
            const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
            setReportHistory(history);
        } catch {
            setReportHistory([]);
        }
    }, []);

    const addReportHistory = useCallback((item: ReportHistoryItem) => {
        setReportHistory((prev) => {
            const newHistory = [item, ...prev].slice(0, 10);
            localStorage.setItem(HISTORY_KEY, JSON.stringify(newHistory));
            return newHistory;
        });
    }, []);

    const clearReportHistory = useCallback(() => {
        localStorage.removeItem(HISTORY_KEY);
        setReportHistory([]);
    }, []);

    return {
        reportHistory,
        addReportHistory,
        clearReportHistory,
    };
}
