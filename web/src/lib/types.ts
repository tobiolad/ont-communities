export interface StatusCount {
  status_name: string;
  count: number;
}

export interface RegionCount {
  region_name: string | null;
  count: number;
}

export interface MinistryCount {
  ministry_name: string;
  count: number;
}

export interface BudgetSummary {
  disclosed_count: number;
  undisclosed_count: number;
  disclosed_sum: number | null;
}

export interface TargetWindowRow {
  status_name: string;
  target_window_passed: boolean;
  count: number;
}

export interface DataCompleteness {
  missing_community: number;
  missing_region: number;
  missing_coordinates: number;
  multi_point_coordinates: number;
  target_date_unknown: number;
  target_date_invalid: number;
}

export interface OverviewResponse {
  total_projects: number;
  by_status: StatusCount[];
  by_region: RegionCount[];
  by_ministry: MinistryCount[];
  budget: BudgetSummary;
  target_window_by_status: TargetWindowRow[];
  data_completeness: DataCompleteness;
}

export interface ProjectSummary {
  project_id: number;
  project_name: string;
  community_name: string | null;
  region_name: string | null;
  ministry_name: string;
  status_name: string;
  estimated_total_budget: number;
  budget_undisclosed: boolean;
  target_completion_date_raw: string;
  target_completion_precision: string;
  target_window_passed: boolean;
  coordinate_status: string;
  website: string | null;
}

export interface ProjectDetail extends ProjectSummary {
  description: string | null;
  result: string | null;
  category: string;
  area: string | null;
  address: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  multi_point_raw: string | null;
  highway_transit_line: string | null;
  target_completion_upper_bound: string | null;
  municipal_funded: boolean;
  provincial_funded: boolean;
  federal_funded: boolean;
  other_funded: boolean;
  batch_id: number;
}

export interface ProjectListResponse {
  total: number;
  page: number;
  page_size: number;
  results: ProjectSummary[];
}

export interface ProjectFilters {
  search?: string;
  region?: string;
  ministry?: string;
  status?: string;
  community?: string;
  has_coordinates?: boolean;
  target_window_passed?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface MapProject {
  project_id: number;
  project_name: string;
  community_name: string | null;
  region_name: string | null;
  ministry_name: string;
  status_name: string;
  latitude: number;
  longitude: number;
  estimated_total_budget: number;
  budget_undisclosed: boolean;
  target_completion_date_raw: string;
  target_window_passed: boolean;
}

export interface MapResponse {
  projects: MapProject[];
  excluded_missing_coordinates: number;
  excluded_multi_point: number;
}

export interface FilterOptions {
  regions: string[];
  ministries: string[];
  statuses: string[];
  communities: string[];
}

export interface InvestmentByRegionRow {
  region_name: string | null;
  project_count: number;
  disclosed_budget_sum: number | null;
  undisclosed_count: number;
}

export interface InvestmentByRegionResponse {
  rows: InvestmentByRegionRow[];
  note: string;
}

export interface InvestmentByMinistryRow {
  ministry_name: string;
  project_count: number;
  disclosed_budget_sum: number | null;
  avg_disclosed_budget: number | null;
}

export interface InvestmentByMinistryResponse {
  rows: InvestmentByMinistryRow[];
  note: string;
}

export interface PastTargetWindowResponse {
  by_status: { status_name: string; count: number }[];
  not_yet_complete: {
    project_id: number;
    project_name: string;
    community_name: string | null;
    ministry_name: string;
    status_name: string;
    target_completion_date_raw: string;
    target_completion_upper_bound: string;
  }[];
  note: string;
}

export interface DataGapsResponse {
  totals: {
    total_projects: number;
    missing_community: number;
    missing_region: number;
    missing_coordinates: number;
    multi_point_coordinates: number;
    budget_undisclosed: number;
    target_date_unknown: number;
    target_date_invalid: number;
    highway_transit_line_populated: number;
  };
  budget_undisclosed_by_region: {
    region_name: string | null;
    undisclosed_count: number;
    total: number;
    undisclosed_pct: number | null;
  }[];
}

export interface DQCheck {
  run_id: number;
  check_name: string;
  severity: "info" | "warning" | "critical";
  status: "pass" | "fail";
  affected_count: number;
  total_count: number;
  details: Record<string, unknown>;
  run_at: string;
}

export interface DataQualityResponse {
  batch_id: number | null;
  checks: DQCheck[];
}

export interface LatestBatch {
  batch_id: number;
  source_url: string;
  source_resource_id: string;
  retrieved_at: string;
  source_last_modified: string | null;
  source_file_hash: string;
  source_row_count: number;
}
