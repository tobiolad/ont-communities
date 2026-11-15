import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { LoadingState, ErrorState, NoteBox } from "../components/StateViews";
import { Link } from "react-router-dom";
import { formatCurrency, formatNumber, formatPercent } from "../lib/format";

export function InsightsPage() {
  const byRegion = useApi(() => api.investmentByRegion(), []);
  const byMinistry = useApi(() => api.investmentByMinistry(), []);
  const pastWindow = useApi(() => api.pastTargetWindow(), []);
  const dataGaps = useApi(() => api.dataGaps(), []);
  const quality = useApi(() => api.dataQuality(), []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Decision intelligence</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Defensible, traceable answers to specific investment and data-completeness questions — every figure
          here matches a query in <code className="text-xs">docs/SQL_EXAMPLES.md</code>.
        </p>
      </div>

      <Section title="Which regions have the largest reported infrastructure investment?">
        {byRegion.status === "loading" && <LoadingState />}
        {byRegion.status === "error" && <ErrorState message={byRegion.error} />}
        {byRegion.status === "success" && (
          <>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byRegion.data.rows.map((r) => ({ ...r, region_name: r.region_name ?? "Not specified" }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dde4df" />
                <XAxis dataKey="region_name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => formatCurrency(v, true)} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Bar dataKey="disclosed_budget_sum" fill="#1f5c45" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <NoteBox>{byRegion.data.note}</NoteBox>
          </>
        )}
      </Section>

      <Section title="Which ministries are receiving the most reported investment?">
        {byMinistry.status === "loading" && <LoadingState />}
        {byMinistry.status === "error" && <ErrorState message={byMinistry.error} />}
        {byMinistry.status === "success" && (
          <>
            <div className="overflow-x-auto rounded-xl border border-border bg-surface">
              <table className="w-full text-sm">
                <thead className="bg-canvas text-left text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th className="px-4 py-2">Ministry</th>
                    <th className="px-4 py-2">Projects</th>
                    <th className="px-4 py-2">Disclosed budget total</th>
                    <th className="px-4 py-2">Avg disclosed budget</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {byMinistry.data.rows.map((r) => (
                    <tr key={r.ministry_name}>
                      <td className="px-4 py-2">{r.ministry_name}</td>
                      <td className="px-4 py-2">{formatNumber(r.project_count)}</td>
                      <td className="px-4 py-2">{formatCurrency(r.disclosed_budget_sum)}</td>
                      <td className="px-4 py-2">{formatCurrency(r.avg_disclosed_budget)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <NoteBox>{byMinistry.data.note}</NoteBox>
          </>
        )}
      </Section>

      <Section title="Which projects have target dates that have passed?">
        {pastWindow.status === "loading" && <LoadingState />}
        {pastWindow.status === "error" && <ErrorState message={pastWindow.error} />}
        {pastWindow.status === "success" && (
          <>
            <NoteBox>{pastWindow.data.note}</NoteBox>
            <p className="mt-3 text-sm font-semibold text-ink-primary">
              {pastWindow.data.not_yet_complete.length} projects have a passed target window and are not yet
              marked Complete:
            </p>
            <div className="mt-2 max-h-80 overflow-y-auto rounded-xl border border-border bg-surface">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-canvas text-left text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th className="px-4 py-2">Project</th>
                    <th className="px-4 py-2">Ministry</th>
                    <th className="px-4 py-2">Status</th>
                    <th className="px-4 py-2">Target (as stated)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pastWindow.data.not_yet_complete.map((row) => (
                    <tr key={row.project_id}>
                      <td className="px-4 py-2">
                        <Link to={`/projects/${row.project_id}`} className="text-brand hover:underline">
                          {row.project_name}
                        </Link>
                      </td>
                      <td className="px-4 py-2 text-ink-secondary">{row.ministry_name}</td>
                      <td className="px-4 py-2 text-ink-secondary">{row.status_name}</td>
                      <td className="px-4 py-2 text-ink-secondary">{row.target_completion_date_raw}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Section>

      <Section title="Where is the available data incomplete?">
        {dataGaps.status === "loading" && <LoadingState />}
        {dataGaps.status === "error" && <ErrorState message={dataGaps.error} />}
        {dataGaps.status === "success" && (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <GapStat label="Budget undisclosed" value={dataGaps.data.totals.budget_undisclosed} total={dataGaps.data.totals.total_projects} />
              <GapStat label="Missing community" value={dataGaps.data.totals.missing_community} total={dataGaps.data.totals.total_projects} />
              <GapStat label="Missing coordinates" value={dataGaps.data.totals.missing_coordinates} total={dataGaps.data.totals.total_projects} />
              <GapStat label="Target date unknown" value={dataGaps.data.totals.target_date_unknown} total={dataGaps.data.totals.total_projects} />
            </div>
            <p className="mt-4 text-sm font-semibold text-ink-primary">Budget non-disclosure rate by region</p>
            <div className="mt-2 overflow-x-auto rounded-xl border border-border bg-surface">
              <table className="w-full text-sm">
                <thead className="bg-canvas text-left text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th className="px-4 py-2">Region</th>
                    <th className="px-4 py-2">Undisclosed / total</th>
                    <th className="px-4 py-2">Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {dataGaps.data.budget_undisclosed_by_region.map((r) => (
                    <tr key={r.region_name ?? "none"}>
                      <td className="px-4 py-2">{r.region_name ?? "Not specified"}</td>
                      <td className="px-4 py-2 text-ink-secondary">
                        {r.undisclosed_count} / {r.total}
                      </td>
                      <td className="px-4 py-2 text-ink-secondary">{r.undisclosed_pct ?? 0}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Section>

      <Section title="Data quality — latest pipeline run">
        {quality.status === "loading" && <LoadingState />}
        {quality.status === "error" && <ErrorState message={quality.error} />}
        {quality.status === "success" && (
          <div className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="w-full text-sm">
              <thead className="bg-canvas text-left text-xs uppercase tracking-wide text-ink-muted">
                <tr>
                  <th className="px-4 py-2">Check</th>
                  <th className="px-4 py-2">Severity</th>
                  <th className="px-4 py-2">Result</th>
                  <th className="px-4 py-2">Affected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {quality.data.checks.map((c) => (
                  <tr key={c.run_id}>
                    <td className="px-4 py-2 font-medium">{c.check_name}</td>
                    <td className="px-4 py-2 capitalize text-ink-secondary">{c.severity}</td>
                    <td className="px-4 py-2">
                      <span className={c.status === "pass" ? "text-signal-high" : "text-signal-low"}>
                        {c.status === "pass" ? "✓ pass" : "✕ fail"}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-ink-secondary">
                      {c.affected_count} / {c.total_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold text-ink-primary">{title}</h2>
      {children}
    </section>
  );
}

function GapStat({ label, value, total }: { label: string; value: number; total: number }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="text-xl font-bold text-ink-primary">{formatNumber(value)}</div>
      <div className="text-xs text-ink-muted">
        {label} ({formatPercent(value, total)})
      </div>
    </div>
  );
}
