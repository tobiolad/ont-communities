# Data Dictionary

Covers every column in `fact_project` and its dimension tables (see [`db/migrations/001_schema.sql`](../db/migrations/001_schema.sql)
for the authoritative DDL). "Source field" names match Ontario's own CKAN field notes, verified live — see
[`docs/AUDIT.md`](AUDIT.md).

## `fact_project`

| Column | Type | Source field | Definition |
|---|---|---|---|
| `project_id` | `SERIAL` | — | Surrogate primary key. |
| `source_row_hash` | `TEXT UNIQUE` | — | SHA-256 of the raw source row (all original field values). The identity used for idempotent re-ingestion — see [Limitations](../README.md#limitations) for what it can't do (track a single project's status changing across snapshots, since the source has no stable project ID). |
| `batch_id` | `INTEGER FK` | — | Which pipeline run loaded this row. Joins to `ingestion_batch` for source URL, retrieval date, file hash. |
| `project_name` | `TEXT` | `Project` | "Summarizes the project in 2-10 words" (source definition). Not unique — the same name legitimately recurs across different locations (e.g. "Affordable Housing" appears in 7+ communities); see `docs/AUDIT.md`. |
| `description` | `TEXT` | `Description` | What's happening. |
| `result` | `TEXT` | `Result` | The outcome/benefit, as stated by the ministry. |
| `category` | `TEXT` | `Category` | Always `"Communities"` in this resource — it's one category slice of Ontario's broader infrastructure disclosure, not every public project. |
| `area` | `TEXT` | `Area` | Legal municipality / First Nation / Local Service Board. Kept on the fact row rather than a dimension because 2 communities have inconsistent area values in the source — forcing it into a dimension would hide that inconsistency. |
| `community_id` | `INTEGER FK` | `Community` | Nullable — 76 of 2,272 current rows have no community. |
| `region_id` | `INTEGER FK` | `Region` | Nullable. Source values are cleaned (whitespace trimmed; literal `"TBD"` treated as unknown, same as blank) — see audit finding on `"Central"` vs `"Central "`. |
| `ministry_id` | `INTEGER FK` | `Supporting Ministry` | Always present in current data. |
| `status_id` | `INTEGER FK, NOT NULL` | `Status` | One of `Complete`, `Under construction`, `Planning` in current data — the pipeline doesn't hardcode this list; `check_status_values` flags anything else as unexpected. |
| `address` / `postal_code` | `TEXT` | `Address` / `Postal Code` | Free text as supplied. |
| `latitude` / `longitude` | `NUMERIC(10,6)` | `Latitude` / `Longitude` | Populated **only** when `coordinate_status = 'single_point'`. Never defaulted to `(0,0)`. |
| `coordinate_status` | `TEXT` | derived | `'single_point'` (2,204 rows) / `'multi_point'` (3 rows — linear/area projects where the source packs several points into one pipe-delimited cell) / `'missing'` (65 rows). |
| `multi_point_raw` | `TEXT` | `Latitude`/`Longitude` | The original pipe-delimited coordinate lists, preserved verbatim when `coordinate_status = 'multi_point'`. |
| `highway_transit_line` | `TEXT` | `Highway / Transit Line` | **Currently `NULL` for all 2,272 rows** in this resource — a documented schema/content change from when the original 2024 project was built; see `docs/AUDIT.md`. |
| `target_completion_date_raw` | `TEXT, NOT NULL` | `Target Completion Date` | The exact source string, always preserved (`"Dec-23"`, `"To Be Determined"`, `"2026"`, etc.). |
| `target_completion_precision` | `TEXT` | derived | `'day'` / `'month'` / `'year'` / `'unknown'` (blank or "To Be Determined") / `'invalid'` (a calendar-impossible date like `"6/31/2026"`). **96% of current rows are `'month'` precision** — there is almost never a true day-level target date in this dataset. |
| `target_completion_upper_bound` | `DATE` | derived | The latest date consistent with the source's stated precision (e.g. `"Dec-23"` → `2023-12-31`). `NULL` when precision is `'unknown'` or `'invalid'`. This is what "target window has passed" means — never a specific day the source didn't actually provide. |
| `estimated_total_budget` | `NUMERIC(14,2), NOT NULL` | `Estimated Total Budget ($)` | **Never coalesced.** The source itself always populates this (never blank), but 47% of current rows are a literal `0`. |
| `budget_undisclosed` | `BOOLEAN` | derived | `TRUE` when `estimated_total_budget = 0`. A real $0 infrastructure project is implausible; this is almost certainly the ministry's placeholder for "not yet publicly disclosed." The raw `0` is never hidden or replaced — this flag exists so analysis can choose to exclude it, not so the number silently disappears. |
| `municipal_funded` / `provincial_funded` / `federal_funded` / `other_funded` | `BOOLEAN` | `Municipal/Provincial/Federal/Other Funding` | The source only ever contains `"Yes"` or blank for these fields (confirmed — never `"No"`). `TRUE` = `"Yes"` was present. `FALSE` means "not indicated on the ministry's disclosure," **not** "confirmed zero dollars from that source." These are **not** dollar amounts — the source provides no per-source funding breakdown, only a disclosure flag. |
| `website` | `TEXT` | `Website` | Populated for 76 of 2,272 rows. |
| `created_at` / `updated_at` | `TIMESTAMPTZ` | — | Row bookkeeping. |

## Dimensions

| Table | Grain | Notes |
|---|---|---|
| `dim_region` | One row per distinct, cleaned region name | 5 current values: Central, East, Northeast, Northwest, Southwest. |
| `dim_community` | One row per distinct community name | 429 current values. Verified 1:1 with region (every community maps to exactly one region in current data) during the audit, before deciding not to force that relationship into the schema — a future data update that breaks this assumption won't silently corrupt anything. |
| `dim_ministry` | One row per distinct supporting ministry | 10 current values. |
| `dim_status` | One row per distinct status | 3 current values. |

## `ingestion_batch`

One row per pipeline run that loaded data: `source_url`, `source_resource_id`, `retrieved_at`, `source_last_modified` (as reported by the CKAN API), `source_file_hash` (MD5 of the downloaded CSV bytes), `source_row_count`. Every fact row links back to the batch that loaded it — full lineage from any number in the dashboard back to exactly which download produced it.

## `dq_check_run`

One row per automated data-quality check, per pipeline run: `check_name`, `severity` (`info`/`warning`/`critical`), `status` (`pass`/`fail`), `affected_count`/`total_count`, and a JSON `details` payload. This is the single source of truth behind both `docs/DATA_QUALITY_REPORT.md` and the dashboard's Data Quality view — they render the same rows, not separately maintained numbers.

## Metric definitions used throughout the app

- **"Target window has passed"** — `target_completion_upper_bound IS NOT NULL AND target_completion_upper_bound < CURRENT_DATE`. This is a statement about a forecast window, not a claim about project performance. A project can be `Complete` and still show "target window passed" (it finished, just not within the originally forecast month) — in current data, **1,864 of 1,873 `Complete` projects** show a passed target window, which is why this metric is never used to imply delay on its own.
- **"Disclosed budget"** — `estimated_total_budget` where `budget_undisclosed = FALSE`. Any sum/average of budget in the dashboard excludes undisclosed ($0) rows by default and says so.
- **"Funded by \<source\>"** — the disclosure flag was `"Yes"`; this does not imply any particular dollar amount or percentage from that source, since the source data doesn't provide one.
