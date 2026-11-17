from fastapi import APIRouter

from ..db import get_cursor

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


@router.get("")
def get_latest_quality_report():
    """
    Returns the real results of the most recent pipeline run's data quality
    checks, read directly from dq_check_run — the exact same rows
    docs/DATA_QUALITY_REPORT.md is generated from.
    """
    with get_cursor() as cur:
        cur.execute("SELECT MAX(batch_id) AS batch_id FROM dq_check_run")
        latest = cur.fetchone()
        batch_id = latest["batch_id"] if latest else None

        if batch_id is None:
            return {"batch_id": None, "checks": []}

        cur.execute(
            """
            SELECT run_id, check_name, severity, status, affected_count, total_count, details, run_at
            FROM dq_check_run
            WHERE batch_id = %s
            ORDER BY run_id
            """,
            (batch_id,),
        )
        checks = cur.fetchall()

    return {"batch_id": batch_id, "checks": checks}
