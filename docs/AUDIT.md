# Repository & Source Audit

Performed before any rebuild work, as required by the project brief. This documents what the original
project did, what's wrong with it specifically, and what the live government source actually looks like
today — verified against the real API, not assumed.

## 1. Original project (2024)

A PostgreSQL + SQL class group project analyzing a static CSV snapshot of the Ontario Builds: Communities
dataset, by **Tobi Oladimeji, Sushma Gouri Deivanayagam, Sachin Suresh, Dwij Shyamsunder, and Surya Amit
Malwade** (credited in the original README and `summary_findings.docx`, preserved below and in the
rebuilt README).

Assets: `sql_scripts.sql` (table creation + 10 analysis queries), `analysis_insights.md` (10 query write-ups
with chart screenshots in `pictures/`), `summary_findings.docx` (full report), `pictures/ONT_ERD.png` (ERD).

**What was genuinely good and is preserved:** the core entity idea (project / status / ministry / community
as separate lookup tables), the shape of several analysis questions (budget by region, projects by ministry,
status breakdown, highest-budget projects), and the original write-ups — kept as historical record in
`docs/original-2024/`, not deleted or rewritten.

## 2. Weaknesses in the original data cleaning (as requested by the brief)

Verified by loading the **current live source** into pandas and testing the original script's assumptions
against real data — not just reading the SQL and guessing.

### Missing-value handling
```sql
UPDATE ont_communities SET Estimated_Total_Budget = COALESCE(Estimated_Total_Budget, 0), ...
```
This replaces unknown budgets with `0`. **1,069 of 2,272 current records (47%) already arrive from the
source with a literal `$0` budget** — almost certainly meaning "not yet publicly disclosed," not "this
infrastructure project costs nothing." The original script's COALESCE-to-zero makes this categorically
worse: it would convert any genuinely missing budget into an indistinguishable extra zero, making 47%+ of
all budget figures silently wrong if summed. The rebuild never coalesces budget to zero and instead keeps
the raw value plus an explicit `budget_undisclosed` flag — see [Data Dictionary](DATA_DICTIONARY.md).

Text columns were coalesced to the **string** `'unknown'`, which is workable but means `'unknown'` then
competes with real category values in every `GROUP BY` — e.g. `Region = 'unknown'` sits next to `Region =
'Central'` as if it were a sixth region, rather than being filterable as "not provided." The rebuild keeps
these as SQL `NULL` and handles them explicitly in queries and the UI.

### Duplicates
```sql
SELECT DISTINCT * FROM ont_communities; -- then truncate + reinsert
```
This only catches **exact full-row duplicates**. On the current live data there are zero full-row
duplicates, so this wouldn't have caught anything today — but it also doesn't protect against a *partial*
duplicate (e.g., the same project appearing twice with one field edited), and it destructively rewrites the
whole table on every run rather than being a targeted, auditable check. The rebuild uses a content-hash
identity key with an idempotent `INSERT ... ON CONFLICT DO NOTHING`, and separately flags (without silently
merging) near-duplicate candidates — see below, "39 same-name records" finding.

**Important false lead, found during this audit:** 39 rows share the same `(Project, Community, Address)`
triplet (e.g., "Affordable Housing" in Cobourg, Milton, Mississauga, Owen Sound, each with a different
budget). These are **not duplicates** — many Ontario infrastructure programs reuse a generic project name
across many distinct locations. A naive dedup on name+location would have wrongly collapsed legitimate,
distinct projects. This is exactly the kind of mistake the brief's "weaknesses in duplicate handling"
question was pointing at, and it runs the other way from the obvious assumption: the risk here is
**over-aggressive** deduplication, not under-aggressive.

### Financial data types
`Estimated_Total_Budget DECIMAL(18,2)` was the right type. But `Municipal_Funding`, `Provincial_Funding`,
`Federal_Funding`, and `Other_Funding` were stored as `VARCHAR(255)` — because **the source does not provide
dollar amounts by funding source at all**. The field notes from Ontario's own data catalogue confirm these
are disclosure flags ("Indicates whether Municipal dollars were allocated to this project on ministry's
disclosure"), populated only with the literal string `"Yes"` or left blank — never a dollar figure, never
`"No"`. Treating these as amounts (or trying to sum them as money) would be inventing data the source
doesn't contain. The rebuild models them as booleans (`municipal_funded`, etc.) and documents this
limitation explicitly wherever funding-source analysis appears in the UI.

### Project status interpretation
The original `summary_findings.docx` describes the "past target completion date" query as finding projects
that are "**behind schedule**" — language the new project's brief explicitly warns against ("do not claim
delayed... without sufficient evidence"). On the live data, this risk is concrete: **Status has only 3
values** (`Complete` 1,873 / `Under construction` 307 / `Planning` 92), so a project can have a past-target
date *and* `Status = Complete` — it finished, just not by the originally forecast window. The rebuild
reports "target window has passed" as a neutral, defensible fact, cross-tabulated with current status, and
never labels a project "delayed" or "underperforming."

## 3. The live source, verified today

Checked directly against the CKAN API (`data.ontario.ca`), not assumed from the README link:

| | |
|---|---|
| Resource | "Ontario Builds: Communities" (`36f92c5b-0c8b-4a4b-b4c5-d15a43894297`), part of dataset `aefd72d3-f67c-44ed-b017-b74e7ecd9258` |
| Status | **Active**, `datastore_active: true` |
| Format | CSV, current file `ontbuilds-communities-20260914.csv` |
| Row count (current) | **2,272** |
| Source `data_last_updated` | 2026-09-16 |
| File hash (md5, confirmed matches download) | `7ebcf40da7a93cd9b46c5e10893ea8c1` |

This is meaningfully larger than whatever static snapshot the 2024 project used, and the schema has changed
in at least one material way:

- **`Highway / Transit Line` is `NULL` for all 2,272 current rows.** The original project's Query 6
  ("Projects in Regions with Highway Transit Lines") would return **zero rows** against today's data — not
  because the SQL is wrong, but because the field is apparently no longer populated for this resource. This
  is a direct, concrete example of "changes in the source schema" that a reproducible pipeline needs to
  detect, not silently ignore.
- `Category` is constant (`"Communities"`, 100% of rows) — this resource is one slice (the "Communities"
  category) of Ontario's broader infrastructure disclosure, not the entire program.

## 4. Additional data quality findings (from full profiling of the live 2,272-row dataset)

| Finding | Evidence |
|---|---|
| Target Completion Date is almost never a full date | 2,184 rows (96%) are month+2-digit-year only (`"Dec-23"`); 47 are year-only; 40 are literal `"To Be Determined"`/`"TBD"`; **1 is a calendar-invalid date, `"6/31/2026"` (June has 30 days)**. Zero rows have an unambiguous full date. |
| Region has inconsistent text values | `"Central"` (482 rows) and `"Central "` — with a trailing space — (1 row) are currently stored as two different values; plus 73 null and 4 literal `"TBD"` regions. |
| Funding flags are "Yes" or blank only | Confirmed across all 4 funding columns — never `"No"`. Absence means "not indicated," not "confirmed $0 from that source." |
| Lat/long are not always single points | 3 rows (linear/area projects, e.g. "South Stormont Tp") store **pipe-delimited lists** of multiple coordinates in one cell, matching the field note "for single point projects (i.e. not a highway project)." These cannot be dropped onto the map as a single pin without misrepresenting the project's extent. |
| Coordinates otherwise complete | 65 of 2,272 rows have no coordinates at all; the remaining 2,204 single-point rows all fall within a sane Ontario bounding box once whitespace is trimmed. |
| No full-row duplicates currently | 0, using exact match across all columns — see the "39 same-name" false-lead note above for why naive dedup is the greater risk here. |
| 10 distinct ministries, 429 communities, 56 areas, 3 statuses | Used directly to size the dimensional model. |

Full reproducible output of this profiling is in [`pipeline/quality/`](../pipeline/quality/) — the same
checks run as part of the pipeline, not a one-off notebook.
