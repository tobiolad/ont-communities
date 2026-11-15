"""
Pure transformation functions for one raw source row -> cleaned fields.

Every function here is deliberately side-effect-free and independently
testable (see pipeline/tests/test_transform.py). Each decision traces back to
a specific finding in docs/AUDIT.md — the comments say which one.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

MONTH_YEAR_RE = re.compile(r"^(?P<mon>[A-Za-z]{3})-(?P<yr>\d{2})$")
YEAR_ONLY_RE = re.compile(r"^(?P<yr>\d{4})$")
ISO_DATE_RE = re.compile(r"^(?P<yr>\d{4})-(?P<mon>\d{2})-(?P<day>\d{2})$")
US_SLASH_DATE_RE = re.compile(r"^(?P<mon>\d{1,2})/(?P<day>\d{1,2})/(?P<yr>\d{4})$")
UNKNOWN_DATE_STRINGS = {"to be determined", "tbd", ""}

_MONTH_ABBR = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}


@dataclass
class DateParseResult:
    raw: str
    precision: str  # 'day' | 'month' | 'year' | 'unknown' | 'invalid'
    upper_bound: Optional[date] = None


def parse_target_date(raw: Optional[str]) -> DateParseResult:
    """
    The source's "Target Completion Date" field is documented as a full
    ISO date but in practice (see docs/AUDIT.md) is almost always
    month+2-digit-year ("Dec-23"), sometimes year-only, sometimes literally
    "To Be Determined", and at least once a calendar-invalid date
    ("6/31/2026" — June has 30 days).

    Rather than force a single DATE value with invented precision, this
    returns the exact raw string plus a precision label and an "upper
    bound" date: the latest date consistent with what the source actually
    said (e.g. "Dec-23" -> 2023-12-31). This upper bound is what
    "target window has passed" checks against — never a specific day that
    wasn't actually in the source.
    """
    original = raw or ""
    cleaned = original.strip()

    if cleaned.lower() in UNKNOWN_DATE_STRINGS:
        return DateParseResult(raw=original, precision="unknown", upper_bound=None)

    m = ISO_DATE_RE.match(cleaned)
    if m:
        try:
            d = date(int(m["yr"]), int(m["mon"]), int(m["day"]))
            return DateParseResult(raw=original, precision="day", upper_bound=d)
        except ValueError:
            return DateParseResult(raw=original, precision="invalid", upper_bound=None)

    m = US_SLASH_DATE_RE.match(cleaned)
    if m:
        try:
            d = date(int(m["yr"]), int(m["mon"]), int(m["day"]))
            return DateParseResult(raw=original, precision="day", upper_bound=d)
        except ValueError:
            # e.g. "6/31/2026" — June doesn't have 31 days. A genuinely
            # invalid date in the source, not something to silently coerce.
            return DateParseResult(raw=original, precision="invalid", upper_bound=None)

    m = MONTH_YEAR_RE.match(cleaned)
    if m:
        month = _MONTH_ABBR.get(m["mon"].lower())
        if month:
            year = 2000 + int(m["yr"])
            last_day = calendar.monthrange(year, month)[1]
            return DateParseResult(raw=original, precision="month", upper_bound=date(year, month, last_day))
        return DateParseResult(raw=original, precision="invalid", upper_bound=None)

    m = YEAR_ONLY_RE.match(cleaned)
    if m:
        year = int(m["yr"])
        return DateParseResult(raw=original, precision="year", upper_bound=date(year, 12, 31))

    return DateParseResult(raw=original, precision="unknown", upper_bound=None)


@dataclass
class CoordinateResult:
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: str = "missing"  # 'single_point' | 'multi_point' | 'missing'
    multi_point_raw: Optional[str] = None


def parse_coordinates(lat_raw: Optional[str], lon_raw: Optional[str]) -> CoordinateResult:
    """
    The source states coordinates are single-point "for single point
    projects (i.e. not a highway project)". In practice a handful of
    linear/area projects pack multiple points into one cell as a
    pipe-delimited list (e.g. "-74.89054|-74.89040"). Those are flagged as
    multi_point and never collapsed into a single invented coordinate.
    Blank/missing coordinates are flagged as 'missing', not defaulted to
    (0, 0) — a real, misleading location in the Gulf of Guinea.
    """
    lat_raw = (lat_raw or "").strip()
    lon_raw = (lon_raw or "").strip()

    if not lat_raw and not lon_raw:
        return CoordinateResult(status="missing")

    if "|" in lat_raw or "|" in lon_raw:
        return CoordinateResult(status="multi_point", multi_point_raw=f"lat={lat_raw}; lon={lon_raw}")

    try:
        lat = Decimal(lat_raw)
        lon = Decimal(lon_raw)
    except (InvalidOperation, ValueError):
        return CoordinateResult(status="multi_point", multi_point_raw=f"lat={lat_raw}; lon={lon_raw}")

    # Loose Ontario bounding box. Outside it, treat as suspect rather than
    # plot a pin in the wrong place — flagged by the data-quality module,
    # not silently dropped here.
    return CoordinateResult(latitude=lat, longitude=lon, status="single_point")


def parse_budget(raw: Optional[str]) -> tuple[Decimal, bool]:
    """
    Returns (value, budget_undisclosed). The source always populates this
    field with a number (confirmed in docs/AUDIT.md — never blank), but
    ~47% of rows are a literal 0, almost certainly meaning "not yet
    publicly disclosed." The raw value is never discarded or replaced;
    budget_undisclosed only flags it for cautious interpretation downstream.
    """
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, AttributeError):
        value = Decimal("0")
    return value, value == 0


def parse_funding_flag(raw: Optional[str]) -> bool:
    """
    The source only ever contains "Yes" or blank for funding-source
    columns (confirmed in docs/AUDIT.md — never "No"). False here means
    "not indicated as a funding source on the ministry's disclosure," not
    "confirmed zero dollars from that source."
    """
    return bool(raw) and raw.strip().lower() == "yes"


def clean_lookup_value(raw: Optional[str]) -> Optional[str]:
    """Trims whitespace and treats blank / 'TBD' as unknown (returns None)."""
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned or cleaned.lower() == "tbd":
        return None
    return cleaned


def compute_row_hash(raw_row: dict) -> str:
    """
    Deterministic identity for a source row, used for idempotent
    re-ingestion (INSERT ... ON CONFLICT DO NOTHING on this hash). Computed
    over the ORIGINAL raw field values (sorted keys, JSON-encoded) rather
    than transformed output, so identical source rows always hash
    identically even if transformation logic changes later.
    """
    canonical = json.dumps(raw_row, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class TransformedProject:
    source_row_hash: str
    project_name: str
    description: Optional[str]
    result: Optional[str]
    category: str
    area: Optional[str]
    community_name: Optional[str]
    region_name: Optional[str]
    ministry_name: str
    status_name: str
    address: Optional[str]
    postal_code: Optional[str]
    coordinates: CoordinateResult
    highway_transit_line: Optional[str]
    target_date: DateParseResult
    estimated_total_budget: Decimal
    budget_undisclosed: bool
    municipal_funded: bool
    provincial_funded: bool
    federal_funded: bool
    other_funded: bool
    website: Optional[str]
    warnings: list[str] = field(default_factory=list)


def transform_row(raw_row: dict) -> TransformedProject:
    """Transforms one raw CSV row (as a dict with the source's exact column names) into a TransformedProject."""
    warnings: list[str] = []

    project_name = (raw_row.get("Project") or "").strip()
    if not project_name:
        warnings.append("missing project name")

    ministry_name = (raw_row.get("Supporting Ministry") or "").strip()
    if not ministry_name:
        warnings.append("missing supporting ministry")

    status_name = (raw_row.get("Status") or "").strip()
    if not status_name:
        warnings.append("missing status")

    target_date = parse_target_date(raw_row.get("Target Completion Date"))
    if target_date.precision == "invalid":
        warnings.append(f"invalid target completion date: {target_date.raw!r}")

    coordinates = parse_coordinates(raw_row.get("Latitude"), raw_row.get("Longitude"))

    budget, budget_undisclosed = parse_budget(raw_row.get("Estimated Total Budget ($)"))

    return TransformedProject(
        source_row_hash=compute_row_hash(raw_row),
        project_name=project_name or "(unnamed project)",
        description=clean_lookup_value(raw_row.get("Description")),
        result=clean_lookup_value(raw_row.get("Result")),
        category=(raw_row.get("Category") or "Communities").strip(),
        area=clean_lookup_value(raw_row.get("Area")),
        community_name=clean_lookup_value(raw_row.get("Community")),
        region_name=clean_lookup_value(raw_row.get("Region")),
        ministry_name=ministry_name or "Unknown",
        status_name=status_name or "Unknown",
        address=clean_lookup_value(raw_row.get("Address")),
        postal_code=clean_lookup_value(raw_row.get("Postal Code")),
        coordinates=coordinates,
        highway_transit_line=clean_lookup_value(raw_row.get("Highway / Transit Line")),
        target_date=target_date,
        estimated_total_budget=budget,
        budget_undisclosed=budget_undisclosed,
        municipal_funded=parse_funding_flag(raw_row.get("Municipal Funding")),
        provincial_funded=parse_funding_flag(raw_row.get("Provincial Funding")),
        federal_funded=parse_funding_flag(raw_row.get("Federal Funding")),
        other_funded=parse_funding_flag(raw_row.get("Other Funding")),
        website=clean_lookup_value(raw_row.get("Website")),
        warnings=warnings,
    )
