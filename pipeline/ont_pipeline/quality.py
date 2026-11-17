"""
Automated data quality checks, run against the live database after each
load. Results are written to dq_check_run (so the API/dashboard can show
exactly what ran) and returned as a list for the markdown report generator.

Every check here answers a specific item from the project brief:
nulls/required fields, duplicates, invalid dates, invalid coordinates,
unexpected status values, financial anomalies, referential integrity,
source schema drift.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

EXPECTED_SOURCE_COLUMNS = [
    "Category", "Supporting Ministry", "Community", "Project", "Status",
    "Target Completion Date", "Description", "Result", "Area", "Region",
    "Address", "Postal Code", "Highway / Transit Line", "Estimated Total Budget ($)",
    "Municipal Funding", "Provincial Funding", "Federal Funding", "Other Funding",
    "Website", "Latitude", "Longitude",
]

KNOWN_STATUS_VALUES = {"Complete", "Under construction", "Planning"}

# Loose bounding box for Ontario, used only to flag suspicious outliers for
# human review — never to silently drop or "correct" a coordinate.
ONTARIO_LAT_RANGE = (41.0, 57.0)
ONTARIO_LON_RANGE = (-96.0, -74.0)


@dataclass
class CheckResult:
    check_name: str
    severity: str  # 'info' | 'warning' | 'critical'
    status: str  # 'pass' | 'fail'
    affected_count: int
    total_count: int
    details: dict[str, Any]

    def to_row(self, batch_id: int) -> tuple:
        return (batch_id, self.check_name, self.severity, self.status, self.affected_count, self.total_count, json.dumps(self.details, default=str))


def _scalar(cur, sql: str, params: tuple = ()) -> int:
    cur.execute(sql, params)
    return cur.fetchone()[0]


def check_required_fields(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    unnamed = _scalar(cur, "SELECT COUNT(*) FROM fact_project WHERE project_name = '(unnamed project)'")
    unknown_ministry = _scalar(
        cur,
        "SELECT COUNT(*) FROM fact_project fp JOIN dim_ministry m ON fp.ministry_id = m.ministry_id WHERE m.ministry_name = 'Unknown'",
    )
    affected = unnamed + unknown_ministry
    return CheckResult(
        "required_fields_present", "critical", "pass" if affected == 0 else "fail",
        affected, total,
        {"unnamed_projects": unnamed, "unknown_ministry": unknown_ministry},
    )


def check_structural_duplicates(cur) -> CheckResult:
    """
    True structural duplicates (identical source rows) are prevented by the
    source_row_hash UNIQUE constraint before they ever reach this check.
    This confirms that constraint is actually doing its job, and separately
    reports same-name/location combinations as context — NOT as failures,
    since the audit found these are usually legitimate distinct projects
    that happen to share a generic name (see docs/AUDIT.md).
    """
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    hash_dupes = _scalar(
        cur,
        "SELECT COUNT(*) FROM (SELECT source_row_hash FROM fact_project GROUP BY source_row_hash HAVING COUNT(*) > 1) t",
    )
    same_name_location = _scalar(
        cur,
        """
        SELECT COUNT(*) FROM (
            SELECT project_name, community_id, address FROM fact_project
            WHERE community_id IS NOT NULL
            GROUP BY project_name, community_id, address HAVING COUNT(*) > 1
        ) t
        """,
    )
    return CheckResult(
        "structural_duplicates", "critical", "pass" if hash_dupes == 0 else "fail",
        hash_dupes, total,
        {
            "exact_content_duplicates": hash_dupes,
            "same_name_community_address_groups": same_name_location,
            "note": "Same-name groups are reported for context only; prior audit confirmed these are typically distinct projects sharing a generic program name, not duplicates.",
        },
    )


def check_target_dates(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    invalid = _scalar(cur, "SELECT COUNT(*) FROM fact_project WHERE target_completion_precision = 'invalid'")
    cur.execute("SELECT target_completion_precision, COUNT(*) FROM fact_project GROUP BY target_completion_precision")
    by_precision = {row[0]: row[1] for row in cur.fetchall()}
    # A single malformed date among thousands of rows doesn't make the
    # dataset unusable — it's a per-row quality issue in the source itself,
    # not a structural failure. Reported as a warning, not critical.
    return CheckResult(
        "target_completion_date_validity", "warning", "pass" if invalid == 0 else "fail",
        invalid, total,
        {"by_precision": by_precision},
    )


def check_coordinates(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    out_of_bounds = _scalar(
        cur,
        """
        SELECT COUNT(*) FROM fact_project
        WHERE coordinate_status = 'single_point'
          AND (latitude NOT BETWEEN %s AND %s OR longitude NOT BETWEEN %s AND %s)
        """,
        (ONTARIO_LAT_RANGE[0], ONTARIO_LAT_RANGE[1], ONTARIO_LON_RANGE[0], ONTARIO_LON_RANGE[1]),
    )
    cur.execute("SELECT coordinate_status, COUNT(*) FROM fact_project GROUP BY coordinate_status")
    by_status = {row[0]: row[1] for row in cur.fetchall()}
    return CheckResult(
        "coordinate_validity", "warning", "pass" if out_of_bounds == 0 else "fail",
        out_of_bounds, total,
        {"by_coordinate_status": by_status, "bounding_box": {"lat": ONTARIO_LAT_RANGE, "lon": ONTARIO_LON_RANGE}},
    )


def check_status_values(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    cur.execute("SELECT status_name, COUNT(*) FROM fact_project fp JOIN dim_status s ON fp.status_id = s.status_id GROUP BY status_name")
    counts = {row[0]: row[1] for row in cur.fetchall()}
    unexpected = {name: n for name, n in counts.items() if name not in KNOWN_STATUS_VALUES}
    affected = sum(unexpected.values())
    return CheckResult(
        "unexpected_status_values", "warning", "pass" if affected == 0 else "fail",
        affected, total,
        {"known_values": sorted(KNOWN_STATUS_VALUES), "observed_values": counts, "unexpected_values": unexpected},
    )


def check_financial_anomalies(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    negative = _scalar(cur, "SELECT COUNT(*) FROM fact_project WHERE estimated_total_budget < 0")
    undisclosed = _scalar(cur, "SELECT COUNT(*) FROM fact_project WHERE budget_undisclosed")
    cur.execute("SELECT MIN(estimated_total_budget), MAX(estimated_total_budget), AVG(estimated_total_budget) FROM fact_project WHERE estimated_total_budget > 0")
    min_b, max_b, avg_b = cur.fetchone()
    return CheckResult(
        "financial_anomalies", "critical", "pass" if negative == 0 else "fail",
        negative, total,
        {
            "negative_budget_count": negative,
            "budget_undisclosed_count": undisclosed,
            "budget_undisclosed_pct": round(100 * undisclosed / total, 1) if total else None,
            "positive_budget_min": min_b, "positive_budget_max": max_b, "positive_budget_avg": float(avg_b) if avg_b else None,
        },
    )


def check_referential_integrity(cur) -> CheckResult:
    total = _scalar(cur, "SELECT COUNT(*) FROM fact_project")
    orphaned_ministry = _scalar(cur, "SELECT COUNT(*) FROM fact_project fp LEFT JOIN dim_ministry m ON fp.ministry_id = m.ministry_id WHERE fp.ministry_id IS NOT NULL AND m.ministry_id IS NULL")
    orphaned_status = _scalar(cur, "SELECT COUNT(*) FROM fact_project fp LEFT JOIN dim_status s ON fp.status_id = s.status_id WHERE s.status_id IS NULL")
    orphaned_community = _scalar(cur, "SELECT COUNT(*) FROM fact_project fp LEFT JOIN dim_community c ON fp.community_id = c.community_id WHERE fp.community_id IS NOT NULL AND c.community_id IS NULL")
    orphaned_region = _scalar(cur, "SELECT COUNT(*) FROM fact_project fp LEFT JOIN dim_region r ON fp.region_id = r.region_id WHERE fp.region_id IS NOT NULL AND r.region_id IS NULL")
    affected = orphaned_ministry + orphaned_status + orphaned_community + orphaned_region
    return CheckResult(
        "referential_integrity", "critical", "pass" if affected == 0 else "fail",
        affected, total,
        {"orphaned_ministry": orphaned_ministry, "orphaned_status": orphaned_status, "orphaned_community": orphaned_community, "orphaned_region": orphaned_region},
    )


def check_source_schema(actual_columns: list[str]) -> CheckResult:
    missing = [c for c in EXPECTED_SOURCE_COLUMNS if c not in actual_columns]
    added = [c for c in actual_columns if c not in EXPECTED_SOURCE_COLUMNS]
    affected = len(missing) + len(added)
    return CheckResult(
        "source_schema_drift", "warning", "pass" if affected == 0 else "fail",
        affected, len(EXPECTED_SOURCE_COLUMNS),
        {"missing_columns": missing, "added_columns": added},
    )


def run_all_checks(conn, batch_id: int, actual_columns: list[str]) -> list[CheckResult]:
    cur = conn.cursor()
    results = [
        check_required_fields(cur),
        check_structural_duplicates(cur),
        check_target_dates(cur),
        check_coordinates(cur),
        check_status_values(cur),
        check_financial_anomalies(cur),
        check_referential_integrity(cur),
        check_source_schema(actual_columns),
    ]
    for result in results:
        cur.execute(
            """
            INSERT INTO dq_check_run (batch_id, check_name, severity, status, affected_count, total_count, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            result.to_row(batch_id),
        )
    conn.commit()
    cur.close()
    return results


def render_markdown_report(batch_id: int, results: list[CheckResult], generated_at: str) -> str:
    lines = [
        "# Data Quality Report",
        "",
        f"Generated: {generated_at}  ",
        f"Ingestion batch: {batch_id}",
        "",
        "Every row below is a real result from the live database for this batch — not a mockup. ",
        "Re-run with `python -m ont_pipeline.run_pipeline` to regenerate.",
        "",
        "| Check | Severity | Status | Affected / Total |",
        "|---|---|---|---|",
    ]
    for r in results:
        icon = "✅" if r.status == "pass" else "❌"
        lines.append(f"| {r.check_name} | {r.severity} | {icon} {r.status} | {r.affected_count} / {r.total_count} |")

    lines.append("")
    lines.append("## Details")
    for r in results:
        lines.append(f"\n### {r.check_name}")
        lines.append(f"- Severity: **{r.severity}**, Status: **{r.status}**")
        lines.append(f"- Affected: {r.affected_count} of {r.total_count}")
        lines.append("```json")
        lines.append(json.dumps(r.details, indent=2, default=str))
        lines.append("```")
    return "\n".join(lines)
