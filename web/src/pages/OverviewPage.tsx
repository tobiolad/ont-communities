import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { LoadingState, ErrorState, NoteBox } from "../components/StateViews";
import { StatCard } from "../components/StatCard";
import { formatCurrency, formatNumber, formatPercent } from "../lib/format";

const STATUS_COLORS: Record<string, string> = {
  Complete: "#1f7a4d",
  "Under construction": "#2563a8",
  Planning: "#a8710a",
};

const REGION_COLOR = "#1f5c45";
const MINISTRY_COLOR = "#2d7a5c";

export function OverviewPage() {
  const overview = useApi(() => api.overview(), []);
  const batch = useApi(() => api.latestBatch(), []);

  if (overview.status === "loading") return <LoadingState label="Loading overview metrics…" />;
  if (overview.status === "error") return <ErrorState message={overview.error} />;

  const data = overview.data;
  const topMinistries = [...data.by_ministry].sort((a, b) => b.count - a.count).slice(0, 6);

  const pastWindowNotComplete = data.target_window_by_status
    .filter((r) => r.target_window_passed && r.status_name !== "Complete")
    .reduce((sum, r) => sum + r.count, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Overview</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          {formatNumber(data.total_projects)} publicly disclosed Ontario infrastructure projects, from the
          Ontario Builds: Communities dataset.
          {batch.status === "success" && (
            <> Last ingested {new Date(batch.data.retrieved_at).toLocaleString("en-CA")}.</>
          )}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Total projects" value={formatNumber(data.total_projects)} />
        <StatCard
          label="Disclosed budget total"
          value={formatCurrency(data.budget.disclosed_sum, true)}
          sublabel={`${formatNumber(data.budget.disclosed_count)} of ${formatNumber(data.total_projects)} projects`}
        />
        <StatCard
          label="Budget not disclosed"
          value={formatPercent(data.budget.undisclosed_count, data.total_projects)}
          sublabel={`${formatNumber(data.budget.undisclosed_count)} projects report $0`}
        />
        <StatCard
          label="Missing coordinates"
          value={formatNumber(data.data_completeness.missing_coordinates)}
          sublabel="excluded from the map"
        />
        <StatCard
          label="Past target window, not complete"
          value={formatNumber(pastWindowNotComplete)}
          sublabel="worth a status follow-up"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Projects by status">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.by_status} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#dde4df" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="status_name" tick={{ fontSize: 12 }} width={120} />
              <Tooltip formatter={(v: number) => formatNumber(v)} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {data.by_status.map((entry) => (
                  <Cell key={entry.status_name} fill={STATUS_COLORS[entry.status_name] || "#7c8a81"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Projects by region">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.by_region.map((r) => ({ ...r, region_name: r.region_name ?? "Not specified" }))}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dde4df" />
              <XAxis dataKey="region_name" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => formatNumber(v)} />
              <Bar dataKey="count" fill={REGION_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <ChartCard title="Top 6 ministries by project count">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={topMinistries} layout="vertical" margin={{ left: 24 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#dde4df" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="ministry_name" tick={{ fontSize: 11 }} width={220} />
            <Tooltip formatter={(v: number) => formatNumber(v)} />
            <Bar dataKey="count" fill={MINISTRY_COLOR} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <NoteBox>
        <strong>Reading "past target window" correctly:</strong> most projects — including the large majority
        already marked Complete — show a passed target window, because target dates in this dataset are
        almost always a month, not a specific day. A passed window is not evidence of delay. The narrower,
        more defensible figure above counts only projects whose target window has passed <em>and</em> which
        aren&apos;t yet marked Complete. See the Decision Intelligence page for the full breakdown.
      </NoteBox>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h2 className="mb-3 text-sm font-semibold text-ink-secondary">{title}</h2>
      {children}
    </div>
  );
}
