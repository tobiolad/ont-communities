import { useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { api } from "../lib/api";
import { useApi } from "../hooks/useApi";
import { LoadingState, ErrorState, NoteBox } from "../components/StateViews";
import { StatusBadge } from "../components/Badge";
import { formatBudgetCell } from "../lib/format";
import type { MapProject } from "../lib/types";

const STATUS_COLORS: Record<string, string> = {
  Complete: "#1f7a4d",
  "Under construction": "#2563a8",
  Planning: "#a8710a",
};

const ONTARIO_CENTER: [number, number] = [49.5, -84.5];

export function MapPage() {
  const [region, setRegion] = useState("");
  const [ministry, setMinistry] = useState("");
  const [status, setStatus] = useState("");

  const filters = useApi(() => api.filters(), []);
  const mapData = useApi(() => api.map({ region, ministry, status }), [region, ministry, status]);
  const [selected, setSelected] = useState<MapProject | null>(null);

  const markers = useMemo(() => (mapData.status === "success" ? mapData.data.projects : []), [mapData]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-ink-primary">Project map</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          Only projects with a single confirmed coordinate are shown — missing or multi-point (linear)
          projects are never guessed onto the map.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <select value={region} onChange={(e) => setRegion(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All regions</option>
          {filters.status === "success" && filters.data.regions.map((r) => <option key={r}>{r}</option>)}
        </select>
        <select value={ministry} onChange={(e) => setMinistry(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All ministries</option>
          {filters.status === "success" && filters.data.ministries.map((m) => <option key={m}>{m}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-lg border border-border bg-surface px-3 py-2 text-sm">
          <option value="">All statuses</option>
          {filters.status === "success" && filters.data.statuses.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      {mapData.status === "loading" && <LoadingState label="Loading map projects…" />}
      {mapData.status === "error" && <ErrorState message={mapData.error} />}

      {mapData.status === "success" && (
        <>
          <NoteBox>
            Showing {markers.length} projects with a mapped location. {mapData.data.excluded_missing_coordinates}{" "}
            projects overall have no coordinates on file, and {mapData.data.excluded_multi_point} are
            linear/area projects the source represents as multiple points rather than one — both are excluded
            here rather than approximated.
          </NoteBox>

          <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
            <div className="h-[560px] overflow-hidden rounded-xl border border-border">
              <MapContainer center={ONTARIO_CENTER} zoom={5} className="h-full w-full">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {markers.map((p) => (
                  <CircleMarker
                    key={p.project_id}
                    center={[p.latitude, p.longitude]}
                    radius={6}
                    pathOptions={{ color: STATUS_COLORS[p.status_name] || "#7c8a81", fillOpacity: 0.7 }}
                    eventHandlers={{ click: () => setSelected(p) }}
                  >
                    <Popup>
                      <p className="font-semibold">{p.project_name}</p>
                      <p>{p.community_name}</p>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>

            <aside className="rounded-xl border border-border bg-surface p-4">
              {!selected ? (
                <p className="text-sm text-ink-muted">Select a marker to see project details.</p>
              ) : (
                <div className="space-y-2">
                  <StatusBadge status={selected.status_name} />
                  <h2 className="text-base font-bold text-ink-primary">{selected.project_name}</h2>
                  <p className="text-sm text-ink-secondary">
                    {selected.community_name} · {selected.region_name ?? "Region not specified"}
                  </p>
                  <p className="text-sm text-ink-secondary">{selected.ministry_name}</p>
                  <dl className="mt-3 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-ink-muted">Reported budget</dt>
                      <dd className="font-medium">{formatBudgetCell(selected.estimated_total_budget, selected.budget_undisclosed)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-ink-muted">Target</dt>
                      <dd className="font-medium">{selected.target_completion_date_raw}</dd>
                    </div>
                  </dl>
                  <a href={`/projects/${selected.project_id}`} className="mt-2 inline-block text-sm font-semibold text-brand hover:underline">
                    Full project details →
                  </a>
                </div>
              )}
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
