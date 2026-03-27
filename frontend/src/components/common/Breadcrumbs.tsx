import { useLocation, Link } from "react-router-dom";
import { Home, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useUIStore } from "@/store/uiStore";
import { categoriesApi } from "@/services/categoriesApi";
import type { Category } from "@/types";

const ROUTE_LABELS: Record<string, string> = {
  students: "O'quvchilar",
  attendance: "Davomat",
  devices: "Qurilmalar",
  reports: "Hisobotlar",
  settings: "Sozlamalar",
  users: "Foydalanuvchilar",
  webhooks: "Webhooklar",
  timetables: "Dars jadvallari",
  "access-groups": "Kirish guruhlari",
  categories: "Kategoriyalar",
};

// Builds ancestor chain for a category: [root, ..., current]
function buildChain(all: Category[], id: number): Category[] {
  const chain: Category[] = [];
  let current: Category | undefined = all.find((c) => c.id === id);
  while (current) {
    chain.unshift(current);
    current = current.parent_id ? all.find((c) => c.id === current!.parent_id) : undefined;
  }
  return chain;
}

function CategoryBreadcrumbs({ categoryId }: { categoryId: number }) {
  const { data } = useQuery({
    queryKey: ["categories", undefined],
    queryFn: () => categoriesApi.list(),
    staleTime: 2 * 60 * 1000,
  });

  const all: Category[] = data?.data?.data ?? [];
  const chain = all.length ? buildChain(all, categoryId) : [];

  return (
    <>
      {/* "A'zolar" segment */}
      <div className="flex items-center gap-1">
        <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
        <Link
          to="/students"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          O'quvchilar
        </Link>
      </div>

      {/* Category chain */}
      {chain.map((cat, i) => (
        <div key={cat.id} className="flex items-center gap-1">
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          {i === chain.length - 1 ? (
            <span className="font-medium text-foreground">{cat.name}</span>
          ) : (
            <Link
              to={`/students/category/${cat.id}`}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {cat.name}
            </Link>
          )}
        </div>
      ))}
    </>
  );
}

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const { pageTitle } = useUIStore();

  if (pathname === "/") return null;

  // /students/category/:id — category breadcrumb
  const categoryMatch = pathname.match(/^\/students\/category\/(\d+)/);
  if (categoryMatch) {
    const categoryId = Number(categoryMatch[1]);
    return (
      <nav className="flex items-center gap-1 border-b bg-card px-6 py-2 text-sm">
        <Link
          to="/"
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          <Home className="h-3.5 w-3.5" />
        </Link>
        <CategoryBreadcrumbs categoryId={categoryId} />
      </nav>
    );
  }

  // Standard segment-based breadcrumbs
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; path: string }[] = [];
  let built = "";

  for (const seg of segments) {
    built += `/${seg}`;
    const label = ROUTE_LABELS[seg];
    if (label) {
      crumbs.push({ label, path: built });
    } else if (/^[0-9a-f-]{8,}$/i.test(seg) && pageTitle) {
      crumbs.push({ label: pageTitle, path: built });
    }
  }

  if (crumbs.length === 0) return null;

  return (
    <nav className="flex items-center gap-1 border-b bg-card px-6 py-2 text-sm">
      <Link
        to="/"
        className="text-muted-foreground transition-colors hover:text-foreground"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>
      {crumbs.map((crumb, i) => (
        <div key={crumb.path} className="flex items-center gap-1">
          <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          {i === crumbs.length - 1 ? (
            <span className="font-medium text-foreground">{crumb.label}</span>
          ) : (
            <Link
              to={crumb.path}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
