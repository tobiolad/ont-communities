import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { StatusBadge } from "../components/Badge";
import { formatBudgetCell, formatNumber } from "../lib/format";
import type { ProjectFilters } from "../lib/types";

const PAGE_SIZE = 20;

const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: "project_name", label: "Project name" },
  { value: "estimated_total_budget", label: "Reported budget" },
  { value: "target_completion_upper_bound", label: "Target date" },
  { value: "region_name", label: "Region" },
  { value: "ministry_name", label: "Ministry" },
];

export function ProjectsPage() {
  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("");
  const [ministry, setMinistry] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState("project_name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  const filters = useApi(() => api.filters(), []);

  const queryFilters: ProjectFilters = {
    search: search || undefined,
    region: region || undefined,
    ministry: ministry || undefined,
    status: status || undefined,
    sort_by: sortBy,
    sort_dir: sortDir,
    page,
    page_size: PAGE_SIZE,
  };

  const projects = useApi(() => api.projects(queryFilters), [search, region, ministry, status, sortBy, sortDir, page]);

  const resetAndSet = (setter: (v: string) => void) => (value: string) => {
    setter(value);
    setPage(1);
  };

  const totalPages = projects.status === "success" ? Math.max(1, Math.ceil(projects.data.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Explore projects</h1>
        <p className="mt-1 text-sm text-ink-secondary">Search, filter, sort, and export the full project list.</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          value={search}
          onChange={(e) => resetAndSet(setSearch)(e.target.value)}
          placeholder="Search project name, description, result…"
          className="min-w-[240px] flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm"
        />
        <select value={region} onChange={(e) => resetAndSet(setRegion)(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All regions</option>
          {filters.status === "success" && filters.data.regions.map((r) => <option key={r}>{r}</option>)}
        </select>
        <select value={ministry} onChange={(e) => resetAndSet(setMinistry)(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All ministries</option>
          {filters.status === "success" && filters.data.ministries.map((m) => <option key={m}>{m}</option>)}
        </select>
        <select value={status} onChange={(e) => resetAndSet(setStatus)(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All statuses</option>
          {filters.status === "success" && filters.data.statuses.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              Sort: {o.label}
            </option>
          ))}
        </select>
        <button
          onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm"
          aria-label="Toggle sort direction"
        >
          {sortDir === "asc" ? "↑ Asc" : "↓ Desc"}
        </button>
        <a
          href={api.exportCsvUrl(queryFilters)}
          className="ml-auto rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-soft"
        >
          ↓ Export filtered CSV
        </a>
      </div>

      {projects.status === "loading" && <LoadingState label="Loading projects…" />}
      {projects.status === "error" && <ErrorState message={projects.error} />}
      {projects.status === "success" && projects.data.results.length === 0 && <EmptyState />}

      {projects.status === "success" && projects.data.results.length > 0 && (
        <>
          <p className="text-sm text-ink-muted">{formatNumber(projects.data.total)} projects match</p>
          <div className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="w-full text-sm">
              <thead className="bg-canvas text-left text-xs uppercase tracking-wide text-ink-muted">
                <tr>
                  <th className="px-4 py-3">Project</th>
                  <th className="px-4 py-3">Region / Community</th>
                  <th className="px-4 py-3">Ministry</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Reported budget</th>
                  <th className="px-4 py-3">Target</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {projects.data.results.map((p) => (
                  <tr key={p.project_id} className="hover:bg-canvas/60">
                    <td className="px-4 py-3">
                      <Link to={`/projects/${p.project_id}`} className="font-medium text-brand hover:underline">
                        {p.project_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-ink-secondary">
                      {p.region_name ?? "—"} / {p.community_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-ink-secondary">{p.ministry_name}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={p.status_name} />
                    </td>
                    <td className="px-4 py-3">{formatBudgetCell(p.estimated_total_budget, p.budget_undisclosed)}</td>
                    <td className="px-4 py-3 text-ink-secondary">{p.target_completion_date_raw}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40"
            >
              ← Previous
            </button>
            <span className="text-ink-muted">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
