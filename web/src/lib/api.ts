import type {
  OverviewResponse,
  ProjectListResponse,
  ProjectFilters,
  ProjectDetail,
  MapResponse,
  FilterOptions,
  InvestmentByRegionResponse,
  InvestmentByMinistryResponse,
  PastTargetWindowResponse,
  DataGapsResponse,
  DataQualityResponse,
  LatestBatch,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function getJSON<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Request to ${path} failed (${res.status}): ${body}`);
  }
  return res.json();
}

export const api = {
  overview: () => getJSON<OverviewResponse>("/api/overview"),
  filters: () => getJSON<FilterOptions>("/api/meta/filters"),
  latestBatch: () => getJSON<LatestBatch>("/api/meta/latest-batch"),
  projects: (filters: ProjectFilters) =>
    getJSON<ProjectListResponse>("/api/projects", filters as Record<string, string | number | boolean | undefined>),
  project: (id: number) => getJSON<ProjectDetail>(`/api/projects/${id}`),
  map: (filters: Pick<ProjectFilters, "search" | "region" | "ministry" | "status" | "community">) =>
    getJSON<MapResponse>("/api/map/projects", filters as Record<string, string | number | boolean | undefined>),
  investmentByRegion: () => getJSON<InvestmentByRegionResponse>("/api/insights/investment-by-region"),
  investmentByMinistry: () => getJSON<InvestmentByMinistryResponse>("/api/insights/investment-by-ministry"),
  pastTargetWindow: () => getJSON<PastTargetWindowResponse>("/api/insights/past-target-window"),
  dataGaps: () => getJSON<DataGapsResponse>("/api/insights/data-gaps"),
  dataQuality: () => getJSON<DataQualityResponse>("/api/data-quality"),
  exportCsvUrl: (filters: ProjectFilters) => {
    const url = new URL("/api/projects/export.csv", API_BASE);
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
    }
    return url.toString();
  },
};
