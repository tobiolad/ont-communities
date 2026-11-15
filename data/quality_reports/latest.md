# Data Quality Report

Generated: 2026-11-15T11:07:57.167734+00:00  
Ingestion batch: 2

Every row below is a real result from the live database for this batch — not a mockup. 
Re-run with `python -m ont_pipeline.run_pipeline` to regenerate.

| Check | Severity | Status | Affected / Total |
|---|---|---|---|
| required_fields_present | critical | ✅ pass | 0 / 2272 |
| structural_duplicates | critical | ✅ pass | 0 / 2272 |
| target_completion_date_validity | warning | ❌ fail | 1 / 2272 |
| coordinate_validity | warning | ✅ pass | 0 / 2272 |
| unexpected_status_values | warning | ✅ pass | 0 / 2272 |
| financial_anomalies | critical | ✅ pass | 0 / 2272 |
| referential_integrity | critical | ✅ pass | 0 / 2272 |
| source_schema_drift | warning | ✅ pass | 0 / 21 |

## Details

### required_fields_present
- Severity: **critical**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "unnamed_projects": 0,
  "unknown_ministry": 0
}
```

### structural_duplicates
- Severity: **critical**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "exact_content_duplicates": 0,
  "same_name_community_address_groups": 33,
  "note": "Same-name groups are reported for context only; prior audit confirmed these are typically distinct projects sharing a generic program name, not duplicates."
}
```

### target_completion_date_validity
- Severity: **warning**, Status: **fail**
- Affected: 1 of 2272
```json
{
  "by_precision": {
    "month": 2184,
    "invalid": 1,
    "year": 47,
    "unknown": 40
  }
}
```

### coordinate_validity
- Severity: **warning**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "by_coordinate_status": {
    "multi_point": 3,
    "missing": 65,
    "single_point": 2204
  },
  "bounding_box": {
    "lat": [
      41.0,
      57.0
    ],
    "lon": [
      -96.0,
      -74.0
    ]
  }
}
```

### unexpected_status_values
- Severity: **warning**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "known_values": [
    "Complete",
    "Planning",
    "Under construction"
  ],
  "observed_values": {
    "Complete": 1873,
    "Planning": 92,
    "Under construction": 307
  },
  "unexpected_values": {}
}
```

### financial_anomalies
- Severity: **critical**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "negative_budget_count": 0,
  "budget_undisclosed_count": 1069,
  "budget_undisclosed_pct": 47.1,
  "positive_budget_min": "1500.00",
  "positive_budget_max": "1536000000.00",
  "positive_budget_avg": 6072438.874480465
}
```

### referential_integrity
- Severity: **critical**, Status: **pass**
- Affected: 0 of 2272
```json
{
  "orphaned_ministry": 0,
  "orphaned_status": 0,
  "orphaned_community": 0,
  "orphaned_region": 0
}
```

### source_schema_drift
- Severity: **warning**, Status: **pass**
- Affected: 0 of 21
```json
{
  "missing_columns": [],
  "added_columns": []
}
```