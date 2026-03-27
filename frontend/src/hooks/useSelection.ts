import { useState, useCallback } from "react";

export function useSelection<T>(items: T[], keyFn: (item: T) => string | number) {
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());

    const toggleSelect = useCallback((id: string | number) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }, []);

    const toggleSelectAll = useCallback(() => {
        setSelectedIds((prev) => {
            if (prev.size === items.length && items.length > 0) {
                return new Set();
            }
            return new Set(items.map(keyFn));
        });
    }, [items, keyFn]);

    const toggleOne = useCallback((id: string | number, checked: boolean) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (checked) {
                next.add(id);
            } else {
                next.delete(id);
            }
            return next;
        });
    }, []);

    const toggleAll = useCallback((checked: boolean) => {
        if (checked) {
            setSelectedIds(new Set(items.map(keyFn)));
        } else {
            setSelectedIds(new Set());
        }
    }, [items, keyFn]);

    const clearSelection = useCallback(() => {
        setSelectedIds(new Set());
    }, []);

    return {
        selectedIds,
        toggleSelect,
        toggleSelectAll,
        toggleOne,
        toggleAll,
        clearSelection,
        isAllSelected: items.length > 0 && selectedIds.size === items.length,
        hasSelection: selectedIds.size > 0,
    };
}
