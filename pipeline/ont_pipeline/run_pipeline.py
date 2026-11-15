"""
CLI entrypoint: Source -> Ingestion -> Validation -> Transformation -> Database -> Quality report.

Usage:
    python -m ont_pipeline.run_pipeline
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from .config import Config
from .fetch import fetch_source_snapshot, save_snapshot
from .transform import transform_row
from .load import get_connection, insert_ingestion_batch, load_transformed_rows
from .quality import run_all_checks, render_markdown_report


def main() -> int:
    print(f"[1/5] Fetching current source snapshot from {Config.SOURCE_API_BASE} ...")
    snapshot = fetch_source_snapshot()
    print(f"      Resource: {snapshot.resource_name!r}, {snapshot.row_count} rows, md5={snapshot.file_hash}")

    csv_path, meta_path = save_snapshot(snapshot)
    print(f"      Saved raw snapshot: {csv_path.name}, {meta_path.name}")

    actual_columns = list(snapshot.rows[0].keys()) if snapshot.rows else []

    print(f"[2/5] Transforming {len(snapshot.rows)} rows ...")
    transformed = [transform_row(row) for row in snapshot.rows]
    total_warnings = sum(len(t.warnings) for t in transformed)
    print(f"      {total_warnings} row-level warnings recorded (see quality report)")

    print("[3/5] Loading into Postgres (idempotent upsert) ...")
    conn = get_connection()
    try:
        cur = conn.cursor()
        batch_id = insert_ingestion_batch(
            cur,
            source_url=snapshot.download_url,
            source_resource_id=snapshot.resource_id,
            retrieved_at=snapshot.retrieved_at,
            source_last_modified=snapshot.source_last_modified,
            source_file_hash=snapshot.file_hash,
            source_row_count=snapshot.row_count,
        )
        conn.commit()
        cur.close()

        summary = load_transformed_rows(conn, batch_id, transformed)
        print(f"      Batch {batch_id}: {summary.inserted} new rows inserted, {summary.already_present} already present (idempotent), {summary.warnings_count} row warnings")

        print("[4/5] Running automated data quality checks ...")
        results = run_all_checks(conn, batch_id, actual_columns)
        for r in results:
            icon = "OK " if r.status == "pass" else "FAIL"
            print(f"      [{icon}] {r.check_name}: {r.affected_count}/{r.total_count} ({r.severity})")

        print("[5/5] Writing data quality report ...")
        report_md = render_markdown_report(batch_id, results, datetime.now(timezone.utc).isoformat())
        Config.QUALITY_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = Config.QUALITY_REPORT_DIR / "latest.md"
        report_path.write_text(report_md, encoding="utf-8")
        print(f"      Wrote {report_path}")

        critical_failures = [r for r in results if r.severity == "critical" and r.status == "fail"]
        if critical_failures:
            print(f"\nPipeline completed with {len(critical_failures)} CRITICAL data quality failure(s).")
            return 1

        print("\nPipeline completed successfully.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
