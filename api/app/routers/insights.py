from fastapi import APIRouter

from ..db import get_cursor

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/investment-by-region")
def investment_by_region():
    """Answers: which regions have the largest reported infrastructure investment?"""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT region_name,
                   COUNT(*) AS project_count,
                   SUM(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed) AS disclosed_budget_sum,
                   COUNT(*) FILTER (WHERE budget_undisclosed) AS undisclosed_count
            FROM v_project
            GROUP BY region_name
            ORDER BY disclosed_budget_sum DESC NULLS LAST
            """
        )
        return {"rows": cur.fetchall(), "note": "disclosed_budget_sum excludes $0 (undisclosed) budgets — see Data Dictionary."}


@router.get("/investment-by-ministry")
def investment_by_ministry():
    """
    Answers: which project categories are receiving funding? In this source
    resource, 'Category' is constant ('Communities') — see docs/AUDIT.md —
    so Supporting Ministry is the closest real substitute for a meaningful
    categorical breakdown of investment.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT ministry_name,
                   COUNT(*) AS project_count,
                   SUM(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed) AS disclosed_budget_sum,
                   ROUND(AVG(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed), 2) AS avg_disclosed_budget
            FROM v_project
            GROUP BY ministry_name
            ORDER BY disclosed_budget_sum DESC NULLS LAST
            """
        )
        return {
            "rows": cur.fetchall(),
            "note": "Category is constant ('Communities') in this source resource, so ministry is shown instead as the meaningful categorical breakdown.",
        }


@router.get("/past-target-window")
def past_target_window():
    """
    Answers: which projects have target dates that have passed? Returned
    alongside current status, and framed as 'target window passed' —
    never as 'delayed' — per docs/AUDIT.md. Completed projects routinely
    show a passed target window because >95% of target dates are
    month-level precision, not day-level.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT status_name, COUNT(*) AS count
            FROM v_project
            WHERE target_window_passed
            GROUP BY status_name
            ORDER BY count DESC
            """
        )
        by_status = cur.fetchall()

        cur.execute(
            """
            SELECT project_id, project_name, community_name, ministry_name, status_name,
                   target_completion_date_raw, target_completion_upper_bound
            FROM v_project
            WHERE target_window_passed AND status_name != 'Complete'
            ORDER BY target_completion_upper_bound ASC
            """
        )
        not_yet_complete = cur.fetchall()

    return {
        "by_status": by_status,
        "not_yet_complete": not_yet_complete,
        "note": (
            "'Target window passed' means the latest date consistent with the source's stated precision "
            "(e.g. the last day of 'Dec-23') is before today. It is not a claim of delay — most Complete "
            "projects show this because dates are usually month-level, not day-level. The "
            "'not_yet_complete' list (status still Planning/Under construction) is the narrower, more "
            "defensible signal worth follow-up."
        ),
    }


@router.get("/data-gaps")
def data_gaps():
    """Answers: where is the available data incomplete?"""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_projects,
                COUNT(*) FILTER (WHERE community_name IS NULL) AS missing_community,
                COUNT(*) FILTER (WHERE region_name IS NULL) AS missing_region,
                COUNT(*) FILTER (WHERE coordinate_status = 'missing') AS missing_coordinates,
                COUNT(*) FILTER (WHERE coordinate_status = 'multi_point') AS multi_point_coordinates,
                COUNT(*) FILTER (WHERE budget_undisclosed) AS budget_undisclosed,
                COUNT(*) FILTER (WHERE target_completion_precision = 'unknown') AS target_date_unknown,
                COUNT(*) FILTER (WHERE target_completion_precision = 'invalid') AS target_date_invalid,
                COUNT(*) FILTER (WHERE highway_transit_line IS NOT NULL) AS highway_transit_line_populated
            FROM v_project
            """
        )
        totals = cur.fetchone()

        cur.execute(
            """
            SELECT region_name, COUNT(*) FILTER (WHERE budget_undisclosed) AS undisclosed_count,
                   COUNT(*) AS total, ROUND(100.0 * COUNT(*) FILTER (WHERE budget_undisclosed) / COUNT(*), 1) AS undisclosed_pct
            FROM v_project
            GROUP BY region_name
            ORDER BY undisclosed_pct DESC NULLS LAST
            """
        )
        undisclosed_by_region = cur.fetchall()

    return {"totals": totals, "budget_undisclosed_by_region": undisclosed_by_region}
