from fastapi import APIRouter

from ..db import get_cursor

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/filters")
def get_filter_options():
    """Returns the real distinct values currently in the database, so the
    UI's filter dropdowns can never offer an option with zero matching rows."""
    with get_cursor() as cur:
        cur.execute("SELECT region_name FROM dim_region ORDER BY region_name")
        regions = [r["region_name"] for r in cur.fetchall()]

        cur.execute("SELECT ministry_name FROM dim_ministry ORDER BY ministry_name")
        ministries = [r["ministry_name"] for r in cur.fetchall()]

        cur.execute("SELECT status_name FROM dim_status ORDER BY status_name")
        statuses = [r["status_name"] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT community_name FROM dim_community ORDER BY community_name")
        communities = [r["community_name"] for r in cur.fetchall()]

    return {
        "regions": regions,
        "ministries": ministries,
        "statuses": statuses,
        "communities": communities,
    }


@router.get("/latest-batch")
def get_latest_batch():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT batch_id, source_url, source_resource_id, retrieved_at,
                   source_last_modified, source_file_hash, source_row_count
            FROM ingestion_batch
            ORDER BY batch_id DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
    return row or {}
