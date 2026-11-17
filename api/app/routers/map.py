from fastapi import APIRouter

from ..db import get_cursor
from .projects import build_filters

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/projects")
def get_map_projects(
    search: str | None = None,
    region: str | None = None,
    ministry: str | None = None,
    status: str | None = None,
    community: str | None = None,
):
    """
    Only projects with a single confirmed coordinate point are returned.
    Projects with missing coordinates, or the 3 multi-point/linear projects
    the source can't express as one pin, are deliberately excluded here
    rather than geocoded or guessed — see docs/AUDIT.md. The overview
    endpoint separately reports how many projects are excluded this way.
    """
    where_sql, params = build_filters(search, region, ministry, status, community, True, None)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT project_id, project_name, community_name, region_name, ministry_name, status_name,
                   latitude, longitude, estimated_total_budget, budget_undisclosed,
                   target_completion_date_raw, target_window_passed
            FROM v_project
            {where_sql}
            """,
            params,
        )
        rows = cur.fetchall()

        cur.execute(
            """
            SELECT COUNT(*) FILTER (WHERE coordinate_status = 'missing') AS missing,
                   COUNT(*) FILTER (WHERE coordinate_status = 'multi_point') AS multi_point
            FROM v_project
            """
        )
        excluded = cur.fetchone()

    return {"projects": rows, "excluded_missing_coordinates": excluded["missing"], "excluded_multi_point": excluded["multi_point"]}
