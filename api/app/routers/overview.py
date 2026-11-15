from fastapi import APIRouter

from ..db import get_cursor

router = APIRouter(prefix="/api/overview", tags=["overview"])


@router.get("")
def get_overview():
    """
    Headline metrics for the overview dashboard. Every figure here is a
    direct aggregate over v_project — the same view the SQL examples in
    docs/SQL_EXAMPLES.md use, so these numbers always reconcile.
    """
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM v_project")
        total_projects = cur.fetchone()["total"]

        cur.execute("SELECT status_name, COUNT(*) AS count FROM v_project GROUP BY status_name ORDER BY count DESC")
        by_status = cur.fetchall()

        cur.execute(
            "SELECT region_name, COUNT(*) AS count FROM v_project GROUP BY region_name ORDER BY count DESC"
        )
        by_region = cur.fetchall()

        cur.execute(
            "SELECT ministry_name, COUNT(*) AS count FROM v_project GROUP BY ministry_name ORDER BY count DESC"
        )
        by_ministry = cur.fetchall()

        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE NOT budget_undisclosed) AS disclosed_count,
                COUNT(*) FILTER (WHERE budget_undisclosed) AS undisclosed_count,
                SUM(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed) AS disclosed_sum
            FROM v_project
            """
        )
        budget = cur.fetchone()

        # "Target window passed" is reported ONLY alongside current status —
        # never as a standalone "delayed" count. See docs/AUDIT.md and
        # docs/SQL_EXAMPLES.md Query 3 for why.
        cur.execute(
            """
            SELECT status_name, target_window_passed, COUNT(*) AS count
            FROM v_project
            GROUP BY status_name, target_window_passed
            ORDER BY status_name, target_window_passed
            """
        )
        target_window_by_status = cur.fetchall()

        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE community_name IS NULL) AS missing_community,
                COUNT(*) FILTER (WHERE region_name IS NULL) AS missing_region,
                COUNT(*) FILTER (WHERE coordinate_status = 'missing') AS missing_coordinates,
                COUNT(*) FILTER (WHERE coordinate_status = 'multi_point') AS multi_point_coordinates,
                COUNT(*) FILTER (WHERE target_completion_precision = 'unknown') AS target_date_unknown,
                COUNT(*) FILTER (WHERE target_completion_precision = 'invalid') AS target_date_invalid
            FROM v_project
            """
        )
        completeness = cur.fetchone()

    return {
        "total_projects": total_projects,
        "by_status": by_status,
        "by_region": by_region,
        "by_ministry": by_ministry,
        "budget": budget,
        "target_window_by_status": target_window_by_status,
        "data_completeness": completeness,
    }
