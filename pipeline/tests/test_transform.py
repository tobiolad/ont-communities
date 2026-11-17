from decimal import Decimal

from ont_pipeline.transform import (
    parse_target_date,
    parse_coordinates,
    parse_budget,
    parse_funding_flag,
    clean_lookup_value,
    compute_row_hash,
    transform_row,
)


class TestParseTargetDate:
    def test_month_year_format(self):
        result = parse_target_date("Dec-23")
        assert result.precision == "month"
        assert result.upper_bound.isoformat() == "2023-12-31"

    def test_month_year_leap_year_february(self):
        result = parse_target_date("Feb-24")
        assert result.precision == "month"
        assert result.upper_bound.isoformat() == "2024-02-29"  # 2024 is a leap year

    def test_year_only(self):
        result = parse_target_date("2026")
        assert result.precision == "year"
        assert result.upper_bound.isoformat() == "2026-12-31"

    def test_to_be_determined(self):
        result = parse_target_date("To Be Determined")
        assert result.precision == "unknown"
        assert result.upper_bound is None

    def test_tbd_case_insensitive(self):
        assert parse_target_date("tbd").precision == "unknown"

    def test_blank(self):
        result = parse_target_date("")
        assert result.precision == "unknown"

    def test_none(self):
        result = parse_target_date(None)
        assert result.precision == "unknown"

    def test_calendar_invalid_date_not_silently_fixed(self):
        """June has 30 days — '6/31/2026' is not a real date and must be
        flagged, not rolled over to July 1 the way naive date libraries do."""
        result = parse_target_date("6/31/2026")
        assert result.precision == "invalid"
        assert result.upper_bound is None
        assert result.raw == "6/31/2026"

    def test_valid_iso_date(self):
        result = parse_target_date("2026-03-15")
        assert result.precision == "day"
        assert result.upper_bound.isoformat() == "2026-03-15"

    def test_invalid_iso_date(self):
        result = parse_target_date("2026-02-30")  # Feb never has 30 days
        assert result.precision == "invalid"

    def test_unrecognized_format_is_unknown_not_invented(self):
        result = parse_target_date("sometime next quarter")
        assert result.precision == "unknown"
        assert result.upper_bound is None


class TestParseCoordinates:
    def test_single_point(self):
        result = parse_coordinates("44.39263", "-79.68474")
        assert result.status == "single_point"
        assert result.latitude == Decimal("44.39263")
        assert result.longitude == Decimal("-79.68474")

    def test_missing_both(self):
        result = parse_coordinates("", "")
        assert result.status == "missing"
        assert result.latitude is None

    def test_missing_none(self):
        result = parse_coordinates(None, None)
        assert result.status == "missing"

    def test_multi_point_pipe_delimited(self):
        result = parse_coordinates("44.1|44.2", "-75.1|-75.2")
        assert result.status == "multi_point"
        assert result.latitude is None
        assert result.longitude is None
        assert "44.1|44.2" in result.multi_point_raw

    def test_never_defaults_to_zero_zero(self):
        """(0, 0) is a real coordinate in the Gulf of Guinea — missing data
        must never be represented as a point on the map."""
        result = parse_coordinates("", "")
        assert result.latitude is None and result.longitude is None
        assert result.status != "single_point"

    def test_unparseable_treated_as_multipoint_not_crash(self):
        result = parse_coordinates("not-a-number", "-79.5")
        assert result.status == "multi_point"


class TestParseBudget:
    def test_positive_value(self):
        value, undisclosed = parse_budget("82500000")
        assert value == Decimal("82500000")
        assert undisclosed is False

    def test_zero_is_flagged_but_preserved(self):
        """The brief explicitly forbids coalescing unknowns to zero — this
        tests the reverse direction: when the SOURCE itself says 0, we must
        not discard that value, only flag it."""
        value, undisclosed = parse_budget("0")
        assert value == Decimal("0")
        assert undisclosed is True

    def test_malformed_defaults_to_zero_and_flags(self):
        value, undisclosed = parse_budget("not-a-number")
        assert value == Decimal("0")
        assert undisclosed is True


class TestParseFundingFlag:
    def test_yes(self):
        assert parse_funding_flag("Yes") is True

    def test_blank(self):
        assert parse_funding_flag("") is False

    def test_none(self):
        assert parse_funding_flag(None) is False

    def test_case_insensitive(self):
        assert parse_funding_flag("yes") is True


class TestCleanLookupValue:
    def test_trims_whitespace(self):
        assert clean_lookup_value("Central ") == "Central"

    def test_tbd_becomes_none(self):
        assert clean_lookup_value("TBD") is None
        assert clean_lookup_value("tbd") is None

    def test_blank_becomes_none(self):
        assert clean_lookup_value("") is None
        assert clean_lookup_value("   ") is None

    def test_none_stays_none(self):
        assert clean_lookup_value(None) is None


class TestRowHash:
    def test_deterministic(self):
        row = {"Project": "Test", "Community": "Toronto"}
        assert compute_row_hash(row) == compute_row_hash(row)

    def test_order_independent(self):
        assert compute_row_hash({"a": 1, "b": 2}) == compute_row_hash({"b": 2, "a": 1})

    def test_different_content_different_hash(self):
        assert compute_row_hash({"a": 1}) != compute_row_hash({"a": 2})


SAMPLE_RAW_ROW = {
    "Category": "Communities",
    "Supporting Ministry": "Attorney General",
    "Community": "Barrie",
    "Project": "Barrie Courthouse - Accessibility",
    "Status": "Under construction",
    "Target Completion Date": "To Be Determined",
    "Description": "Create accessible public entry.",
    "Result": "Improved accessibility.",
    "Area": "Simcoe",
    "Region": "Central",
    "Address": "75 Mulcaster Street",
    "Postal Code": "L4M 3P2",
    "Highway / Transit Line": "",
    "Estimated Total Budget ($)": "0",
    "Municipal Funding": "",
    "Provincial Funding": "Yes",
    "Federal Funding": "",
    "Other Funding": "",
    "Website": "",
    "Latitude": "44.39263",
    "Longitude": "-79.68474",
}


class TestTransformRow:
    def test_full_row(self):
        result = transform_row(SAMPLE_RAW_ROW)
        assert result.project_name == "Barrie Courthouse - Accessibility"
        assert result.ministry_name == "Attorney General"
        assert result.region_name == "Central"
        assert result.estimated_total_budget == Decimal("0")
        assert result.budget_undisclosed is True
        assert result.provincial_funded is True
        assert result.municipal_funded is False
        assert result.coordinates.status == "single_point"
        assert result.target_date.precision == "unknown"
        assert result.warnings == []

    def test_missing_project_name_produces_warning(self):
        row = dict(SAMPLE_RAW_ROW)
        row["Project"] = ""
        result = transform_row(row)
        assert "missing project name" in result.warnings
        assert result.project_name == "(unnamed project)"
