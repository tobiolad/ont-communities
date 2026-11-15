"""Fetches the current source file from Ontario's open data CKAN API and
saves a documented raw snapshot (the actual CSV bytes, plus retrieval
metadata as JSON) before any processing happens.

The Open Government Licence – Ontario permits redistribution, so the raw
snapshot is committed to the repo under data/raw/ rather than only described.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from .config import Config


@dataclass
class SourceSnapshot:
    csv_text: str
    rows: list[dict]
    resource_id: str
    download_url: str
    retrieved_at: str
    source_last_modified: str | None
    file_hash: str
    row_count: int
    resource_name: str


def fetch_resource_metadata(resource_id: str, api_base: str) -> dict:
    resp = requests.get(f"{api_base}/resource_show", params={"id": resource_id}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN resource_show failed for {resource_id}: {payload}")
    return payload["result"]


def fetch_source_snapshot(resource_id: str | None = None, api_base: str | None = None) -> SourceSnapshot:
    resource_id = resource_id or Config.SOURCE_RESOURCE_ID
    api_base = api_base or Config.SOURCE_API_BASE

    meta = fetch_resource_metadata(resource_id, api_base)
    download_url = meta["url"]

    csv_resp = requests.get(download_url, timeout=60)
    csv_resp.raise_for_status()
    csv_bytes = csv_resp.content
    csv_text = csv_bytes.decode("utf-8-sig")  # source ships a UTF-8 BOM

    rows = list(csv.DictReader(io.StringIO(csv_text)))

    return SourceSnapshot(
        csv_text=csv_text,
        rows=rows,
        resource_id=resource_id,
        download_url=download_url,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        source_last_modified=meta.get("last_modified"),
        file_hash=hashlib.md5(csv_bytes).hexdigest(),
        row_count=len(rows),
        resource_name=meta.get("name", ""),
    )


def save_snapshot(snapshot: SourceSnapshot, raw_dir: Path | None = None) -> tuple[Path, Path]:
    """Writes the CSV and a metadata sidecar JSON, named by retrieval date."""
    raw_dir = raw_dir or Config.RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    date_stamp = snapshot.retrieved_at[:10]
    csv_path = raw_dir / f"ontbuilds-communities-{date_stamp}.csv"
    meta_path = raw_dir / f"ontbuilds-communities-{date_stamp}.meta.json"

    csv_path.write_text(snapshot.csv_text, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "resource_id": snapshot.resource_id,
                "resource_name": snapshot.resource_name,
                "download_url": snapshot.download_url,
                "retrieved_at": snapshot.retrieved_at,
                "source_last_modified": snapshot.source_last_modified,
                "file_hash_md5": snapshot.file_hash,
                "row_count": snapshot.row_count,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return csv_path, meta_path
