"""
Integration tests against a running Postgres instance with the pipeline
already run once (see README "Reproducing locally"). These exercise the
real database, not mocks — consistent with the project's "no fabricated
results" requirement.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_overview_shape_and_totals_reconcile():
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_projects"] > 0
    status_sum = sum(row["count"] for row in data["by_status"])
    assert status_sum == data["total_projects"]


def test_meta_filters_only_returns_values_present_in_data():
    resp = client.get("/api/meta/filters")
    assert resp.status_code == 200
    data = resp.json()
    assert "Central" in data["regions"]
    assert "unknown" not in [r.lower() for r in data["regions"]]  # no placeholder values leaked into filters


def test_projects_list_pagination():
    resp = client.get("/api/projects", params={"page": 1, "page_size": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) <= 5
    assert data["page"] == 1


def test_projects_filter_by_region():
    resp = client.get("/api/projects", params={"region": "Central", "page_size": 500})
    data = resp.json()
    assert data["total"] > 0
    assert all(p["region_name"] == "Central" for p in data["results"])


def test_projects_invalid_sort_column_rejected():
    resp = client.get("/api/projects", params={"sort_by": "'; DROP TABLE fact_project; --"})
    assert resp.status_code == 400


def test_project_detail_not_found():
    resp = client.get("/api/projects/99999999")
    assert resp.status_code == 404


def test_project_detail_found():
    listing = client.get("/api/projects", params={"page_size": 1}).json()
    project_id = listing["results"][0]["project_id"]
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["project_id"] == project_id


def test_export_csv_returns_csv_content_type():
    resp = client.get("/api/projects/export.csv", params={"region": "Central"})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "project_name" in resp.text.splitlines()[0]


def test_map_projects_excludes_missing_and_multipoint():
    resp = client.get("/api/map/projects")
    data = resp.json()
    assert data["excluded_missing_coordinates"] > 0
    assert data["excluded_multi_point"] > 0
    # Every returned project must have real numeric coordinates, never (0, 0)
    for p in data["projects"]:
        assert p["latitude"] is not None and p["longitude"] is not None
        assert not (p["latitude"] == 0 and p["longitude"] == 0)


def test_insights_past_target_window_never_labels_delayed():
    resp = client.get("/api/insights/past-target-window")
    data = resp.json()
    assert "delayed" not in data["note"].lower() or "not a claim of delay" in data["note"].lower()
    assert "not_yet_complete" in data


def test_insights_investment_by_region_excludes_undisclosed_from_sum():
    resp = client.get("/api/insights/investment-by-region")
    data = resp.json()
    assert len(data["rows"]) > 0
    assert "note" in data


def test_data_quality_report_has_real_results():
    resp = client.get("/api/data-quality")
    data = resp.json()
    assert data["batch_id"] is not None
    check_names = {c["check_name"] for c in data["checks"]}
    assert "referential_integrity" in check_names
    assert "financial_anomalies" in check_names
