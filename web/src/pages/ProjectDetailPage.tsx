import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { LoadingState, ErrorState } from "../components/StateViews";
import { StatusBadge, Badge } from "../components/Badge";
import { formatBudgetCell } from "../lib/format";

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const project = useApi(() => api.project(Number(id)), [id]);

  if (project.status === "loading") return <LoadingState label="Loading project…" />;
  if (project.status === "error") return <ErrorState message={project.error} />;

  const p = project.data;
  const fundingSources = [
    p.municipal_funded && "Municipal",
    p.provincial_funded && "Provincial",
    p.federal_funded && "Federal",
    p.other_funded && "Other",
  ].filter(Boolean) as string[];

  return (
    <div className="max-w-3xl space-y-5">
      <Link to="/projects" className="text-sm text-ink-muted hover:text-ink-primary">
        ← Back to projects
      </Link>

      <div className="rounded-xl border border-border bg-surface p-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
          {p.region_name ?? "Region not specified"} · {p.community_name ?? "Community not specified"}
        </p>
        <h1 className="mt-1 text-2xl font-bold text-ink-primary">{p.project_name}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusBadge status={p.status_name} />
          <Badge label={p.ministry_name} />
          {p.target_window_passed && p.status_name !== "Complete" && (
            <Badge label="Target window passed" tone="medium" />
          )}
        </div>

        {p.description && <p className="mt-4 text-sm text-ink-secondary">{p.description}</p>}
        {p.result && (
          <div className="mt-3 border-l-2 border-brand/40 pl-3 text-sm text-ink-secondary">
            <span className="font-semibold text-ink-primary">Stated result: </span>
            {p.result}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-xl border border-border bg-surface p-6 sm:grid-cols-3">
        <Field label="Reported budget" value={formatBudgetCell(p.estimated_total_budget, p.budget_undisclosed)} />
        <Field label="Target completion" value={p.target_completion_date_raw} />
        <Field label="Address" value={p.address ?? "Not provided"} />
        <Field label="Postal code" value={p.postal_code ?? "Not provided"} />
        <Field label="Funding sources" value={fundingSources.length ? fundingSources.join(", ") : "None disclosed"} />
        <Field label="Highway/transit line" value={p.highway_transit_line ?? "Not applicable / not provided"} />
      </div>

      {p.website && (
        <a href={p.website} target="_blank" rel="noreferrer" className="inline-block text-sm font-semibold text-brand hover:underline">
          Official project page ↗
        </a>
      )}

      {p.coordinate_status === "multi_point" && (
        <p className="text-sm text-ink-muted">
          This project spans multiple points (e.g. a highway or area project) and isn&apos;t shown as a single
          pin on the map. Raw coordinate data: <code className="text-xs">{p.multi_point_raw}</code>
        </p>
      )}
      {p.coordinate_status === "missing" && (
        <p className="text-sm text-ink-muted">No coordinates were provided for this project in the source data.</p>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-ink-muted">{label}</dt>
      <dd className="mt-1 text-sm text-ink-primary">{value}</dd>
    </div>
  );
}
