import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..db import get_cursor

router = APIRouter(prefix="/api/projects", tags=["projects"])

SORTABLE_COLUMNS = {
    "project_name": "project_name",
    "region_name": "region_name",
    "ministry_name": "ministry_name",
    "status_name": "status_name",
    "estimated_total_budget": "estimated_total_budget",
    "target_completion_upper_bound": "target_completion_upper_bound",
}


def build_filters(
    search: str | None,
    region: str | None,
    ministry: str | None,
    status: str | None,
    community: str | None,
    has_coordinates: bool | None,
    target_window_passed: bool | None,
):
    clauses = []
    params: list = []

    if search:
        clauses.append("(project_name ILIKE %s OR description ILIKE %s OR result ILIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if region:
        clauses.append("region_name = %s")
        params.append(region)
    if ministry:
        clauses.append("ministry_name = %s")
        params.append(ministry)
    if status:
        clauses.append("status_name = %s")
        params.append(status)
    if community:
        clauses.append("community_name = %s")
        params.append(community)
    if has_coordinates is True:
        clauses.append("coordinate_status = 'single_point'")
    elif has_coordinates is False:
        clauses.append("coordinate_status != 'single_point'")
    if target_window_passed is not None:
        clauses.append("target_window_passed = %s")
        params.append(target_window_passed)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


@router.get("")
def list_projects(
    search: str | None = None,
    region: str | None = None,
    ministry: str | None = None,
    status: str | None = None,
    community: str | None = None,
    has_coordinates: bool | None = None,
    target_window_passed: bool | None = None,
    sort_by: str = "project_name",
    sort_dir: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
):
    if sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(400, f"sort_by must be one of {sorted(SORTABLE_COLUMNS)}")
    if sort_dir not in ("asc", "desc"):
        raise HTTPException(400, "sort_dir must be 'asc' or 'desc'")

    where_sql, params = build_filters(search, region, ministry, status, community, has_coordinates, target_window_passed)
    order_col = SORTABLE_COLUMNS[sort_by]
    offset = (page - 1) * page_size

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM v_project {where_sql}", params)
        total = cur.fetchone()["total"]

        cur.execute(
            f"""
            SELECT project_id, project_name, community_name, region_name, ministry_name, status_name,
                   estimated_total_budget, budget_undisclosed, target_completion_date_raw,
                   target_completion_precision, target_window_passed, coordinate_status, website
            FROM v_project
            {where_sql}
            ORDER BY {order_col} {sort_dir} NULLS LAST, project_id ASC
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, offset],
        )
        rows = cur.fetchall()

    return {"total": total, "page": page, "page_size": page_size, "results": rows}


@router.get("/export.csv")
def export_projects_csv(
    search: str | None = None,
    region: str | None = None,
    ministry: str | None = None,
    status: str | None = None,
    community: str | None = None,
    has_coordinates: bool | None = None,
    target_window_passed: bool | None = None,
):
    """Exports the SAME filtered set the table shows — no separate query path
    that could silently drift from what the user sees on screen."""
    where_sql, params = build_filters(search, region, ministry, status, community, has_coordinates, target_window_passed)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT project_name, community_name, region_name, ministry_name, status_name,
                   estimated_total_budget, budget_undisclosed, target_completion_date_raw,
                   target_completion_precision, target_window_passed, address, postal_code,
                   latitude, longitude, coordinate_status, municipal_funded, provincial_funded,
                   federal_funded, other_funded, website
            FROM v_project
            {where_sql}
            ORDER BY project_name ASC
            """,
            params,
        )
        rows = cur.fetchall()

    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ontario_infrastructure_projects.csv"},
    )


@router.get("/{project_id}")
def get_project(project_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM v_project WHERE project_id = %s", (project_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return row
