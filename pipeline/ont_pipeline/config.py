"""Configuration loaded from environment variables. No hardcoded credentials."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


class Config:
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://ont_app:ont_dev_password@localhost:5432/ont_infrastructure",
    )
    SOURCE_RESOURCE_ID: str = os.environ.get(
        "SOURCE_RESOURCE_ID", "36f92c5b-0c8b-4a4b-b4c5-d15a43894297"
    )
    SOURCE_API_BASE: str = os.environ.get(
        "SOURCE_API_BASE", "https://data.ontario.ca/api/3/action"
    )
    RAW_DATA_DIR: Path = REPO_ROOT / "data" / "raw"
    QUALITY_REPORT_DIR: Path = REPO_ROOT / "data" / "quality_reports"
