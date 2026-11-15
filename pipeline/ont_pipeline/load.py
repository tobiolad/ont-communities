"""Loads transformed rows into Postgres. Idempotent: re-running against the
same source content inserts zero additional rows (see docs/AUDIT.md,
"Duplicates", for why a content hash is used instead of a name/location key).
"""
from __future__ import annotations

from dataclasses import dataclass

import psycopg2
import psycopg2.extras

from .config import Config
from .transform import TransformedProject


def get_connection(database_url: str | None = None):
    return psycopg2.connect(database_url or Config.DATABASE_URL)


def get_or_create_dim(cur, table: str, name_col: str, pk_col: str, value: str | None, cache: dict) -> int | None:
    if value is None:
        return None
    if value in cache:
        return cache[value]
    cur.execute(f"SELECT {pk_col} FROM {table} WHERE {name_col} = %s", (value,))
    row = cur.fetchone()
    if row:
        cache[value] = row[0]
        return row[0]
    cur.execute(
        f"INSERT INTO {table} ({name_col}) VALUES (%s) ON CONFLICT ({name_col}) DO UPDATE SET {name_col}=EXCLUDED.{name_col} RETURNING {pk_col}",
        (value,),
    )
    new_id = cur.fetchone()[0]
    cache[value] = new_id
    return new_id


def insert_ingestion_batch(
    cur,
    source_url: str,
    source_resource_id: str,
    retrieved_at: str,
    source_last_modified: str | None,
    source_file_hash: str,
    source_row_count: int,
    notes: str | None = None,
) -> int:
    cur.execute(
        """
        INSERT INTO ingestion_batch
            (source_url, source_resource_id, retrieved_at, source_last_modified, source_file_hash, source_row_count, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING batch_id
        """,
        (source_url, source_resource_id, retrieved_at, source_last_modified, source_file_hash, source_row_count, notes),
    )
    return cur.fetchone()[0]


@dataclass
class LoadSummary:
    total_rows: int
    inserted: int
    already_present: int
    warnings_count: int


def load_transformed_rows(conn, batch_id: int, transformed_rows: list[TransformedProject]) -> LoadSummary:
    cur = conn.cursor()
    community_cache: dict = {}
    region_cache: dict = {}
    ministry_cache: dict = {}
    status_cache: dict = {}

    inserted = 0
    already_present = 0
    warnings_count = 0

    for row in transformed_rows:
        community_id = get_or_create_dim(cur, "dim_community", "community_name", "community_id", row.community_name, community_cache)
        region_id = get_or_create_dim(cur, "dim_region", "region_name", "region_id", row.region_name, region_cache)
        ministry_id = get_or_create_dim(cur, "dim_ministry", "ministry_name", "ministry_id", row.ministry_name, ministry_cache)
        status_id = get_or_create_dim(cur, "dim_status", "status_name", "status_id", row.status_name, status_cache)

        warnings_count += len(row.warnings)

        cur.execute(
            """
            INSERT INTO fact_project (
                source_row_hash, batch_id, project_name, description, result, category,
                area, community_id, region_id, ministry_id, status_id,
                address, postal_code, latitude, longitude, coordinate_status, multi_point_raw,
                highway_transit_line,
                target_completion_date_raw, target_completion_precision, target_completion_upper_bound,
                estimated_total_budget, budget_undisclosed,
                municipal_funded, provincial_funded, federal_funded, other_funded,
                website
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s
            )
            ON CONFLICT (source_row_hash) DO NOTHING
            """,
            (
                row.source_row_hash, batch_id, row.project_name, row.description, row.result, row.category,
                row.area, community_id, region_id, ministry_id, status_id,
                row.address, row.postal_code, row.coordinates.latitude, row.coordinates.longitude,
                row.coordinates.status, row.coordinates.multi_point_raw,
                row.highway_transit_line,
                row.target_date.raw, row.target_date.precision, row.target_date.upper_bound,
                row.estimated_total_budget, row.budget_undisclosed,
                row.municipal_funded, row.provincial_funded, row.federal_funded, row.other_funded,
                row.website,
            ),
        )
        if cur.rowcount == 1:
            inserted += 1
        else:
            already_present += 1

    conn.commit()
    cur.close()
    return LoadSummary(
        total_rows=len(transformed_rows),
        inserted=inserted,
        already_present=already_present,
        warnings_count=warnings_count,
    )
