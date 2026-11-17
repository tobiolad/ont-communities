# SQL Analysis Examples

All queries below run against `v_project` (see [`db/migrations/002_views.sql`](../db/migrations/002_views.sql)),
the same view the API reads from — so these numbers and the dashboard's numbers are guaranteed to match.
**Output shown is real, captured by actually running these queries against the live-ingested dataset on
2026-11-15** (2,272 projects) — not illustrative or invented.

## 1. Projects by status

```sql
SELECT status_name, COUNT(*)
FROM v_project
GROUP BY status_name
ORDER BY COUNT(*) DESC;
```
```
    status_name     | count
---------------------+-------
 Complete            |  1873
 Under construction  |   307
 Planning            |    92
```

## 2. Project count and disclosed budget by region

Deliberately separates "how many projects" from "how much disclosed budget," and reports how many of each
region's projects have an undisclosed ($0) budget rather than silently folding them into the sum.

```sql
SELECT region_name,
       COUNT(*) AS project_count,
       SUM(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed) AS disclosed_budget_sum,
       COUNT(*) FILTER (WHERE budget_undisclosed) AS undisclosed_budget_count
FROM v_project
GROUP BY region_name
ORDER BY disclosed_budget_sum DESC NULLS LAST;
```
```
 region_name | project_count | disclosed_budget_sum | undisclosed_budget_count
-------------+---------------+-----------------------+--------------------------
 Central     |           483 |       4,381,340,932   |                      184
 Northwest   |           320 |       1,453,459,657   |                      142
 East        |           428 |         817,810,199   |                      201
 Southwest   |           476 |         342,872,150   |                      225
 Northeast   |           488 |         295,474,601   |                      259
 (no region) |            77 |          14,186,427   |                       58
```
**Reading this correctly:** Central has the largest disclosed investment, but it also has the most projects
and among the lowest undisclosed-budget rates — part of why its total is largest is that more of its budgets
are actually visible to sum. Northeast has the most projects of any region but the smallest disclosed total,
largely because 53% of its projects have an undisclosed budget. This is a data-completeness story as much as
an investment-distribution one — see [Query 5](#5-data-completeness-overview).

## 3. "Target window passed," cross-tabbed by current status

```sql
SELECT status_name, target_window_passed, COUNT(*)
FROM v_project
GROUP BY status_name, target_window_passed
ORDER BY status_name, target_window_passed;
```
```
    status_name     | target_window_passed | count
---------------------+-----------------------+-------
 Complete            | false                 |     9
 Complete            | true                  |  1864
 Planning            | false                 |    84
 Planning            | true                  |     8
 Under construction  | false                 |   265
 Under construction  | true                  |    42
```
**Why this matters, and what it doesn't show:** 1,864 of 1,873 `Complete` projects show a passed target
window — because almost every target date in this dataset is only a month, not a day (see the Data
Dictionary), a project routinely finishes after the stated month ends even when nothing went wrong. The
numbers worth actually looking at are the **42 `Under construction`** and **8 `Planning`** projects whose
target window has passed and which are *not yet marked complete* — that's a defensible, narrow signal worth
a human follow-up. It is not evidence that those 50 projects are "delayed," only that their originally
forecast window has elapsed without a status update to `Complete`.

## 4. Funding source disclosure prevalence

```sql
SELECT
  ROUND(100.0 * COUNT(*) FILTER (WHERE municipal_funded)  / COUNT(*), 1) AS pct_municipal,
  ROUND(100.0 * COUNT(*) FILTER (WHERE provincial_funded) / COUNT(*), 1) AS pct_provincial,
  ROUND(100.0 * COUNT(*) FILTER (WHERE federal_funded)    / COUNT(*), 1) AS pct_federal,
  ROUND(100.0 * COUNT(*) FILTER (WHERE other_funded)      / COUNT(*), 1) AS pct_other
FROM v_project;
```
```
 pct_municipal | pct_provincial | pct_federal | pct_other
----------------+-----------------+-------------+-----------
          49.0 |           98.5 |        46.9 |      21.7
```
These are **disclosure rates**, not dollar shares — the source states only whether each funding source
contributed, never how much. 98.5% provincial disclosure makes sense: this is a provincial ministry program.

## 5. Data completeness overview

```sql
SELECT
  COUNT(*) AS total_projects,
  COUNT(*) FILTER (WHERE community_name IS NULL) AS missing_community,
  COUNT(*) FILTER (WHERE region_name IS NULL) AS missing_region,
  COUNT(*) FILTER (WHERE coordinate_status = 'missing') AS missing_coordinates,
  COUNT(*) FILTER (WHERE coordinate_status = 'multi_point') AS multi_point_coordinates,
  COUNT(*) FILTER (WHERE budget_undisclosed) AS budget_undisclosed,
  COUNT(*) FILTER (WHERE target_completion_precision = 'unknown') AS target_date_unknown,
  COUNT(*) FILTER (WHERE target_completion_precision = 'invalid') AS target_date_invalid
FROM v_project;
```
```
 total_projects | missing_community | missing_region | missing_coordinates | multi_point | budget_undisclosed | target_unknown | target_invalid
-----------------+--------------------+-----------------+----------------------+-------------+---------------------+-----------------+-----------------
            2272 |                 76 |              77 |                   65 |           3 |                1069 |              40 |               1
```
**47% of all projects have an undisclosed budget.** Any headline "$X billion invested" figure that doesn't
separate this out is materially misleading — the dashboard always shows disclosed-vs-undisclosed counts
alongside any budget total.

## 6. Top 5 disclosed-budget projects

```sql
SELECT project_name, community_name, estimated_total_budget
FROM v_project
WHERE NOT budget_undisclosed
ORDER BY estimated_total_budget DESC
LIMIT 5;
```
```
            project_name            | community_name | estimated_total_budget
--------------------------------------+-----------------+------------------------
 MacDonald Block Reconstruction      | Toronto         |          1,536,000,000
 Thunder Bay Correctional Complex    | Thunder Bay     |          1,200,000,000
 New courthouse in Toronto           | Toronto         |            956,400,000
 PanAm/Parapan Athletes' Village     | Toronto         |            687,000,000
 CHEO Integrated Treatment Centre    | Ottawa          |            371,370,000
```

## 7. Disclosed budget by ministry

```sql
SELECT ministry_name, COUNT(*) AS project_count,
       SUM(estimated_total_budget) FILTER (WHERE NOT budget_undisclosed) AS disclosed_sum
FROM v_project
GROUP BY ministry_name
ORDER BY disclosed_sum DESC NULLS LAST;
```
```
                ministry_name                       | project_count | disclosed_sum
------------------------------------------------------+---------------+----------------
 Infrastructure                                       |          1688 |   2,271,490,727
 Solicitor General                                    |             8 |   1,389,300,000
 Attorney General                                     |            31 |   1,121,400,000
 Tourism, Culture and Sport                           |           170 |   1,055,884,500
 Children, Community and Social Services              |            51 |     758,296,747
 Municipal Affairs and Housing                        |           165 |     370,120,023
 Northern Development                                 |           141 |     267,938,118
 Labour, Immigration, Training and Skills Development |            12 |      36,213,851
 Environment, Conservation and Parks                  |             3 |      34,500,000
 Transportation                                       |             3 |     (all undisclosed)
```
**Infrastructure runs the most projects by far (1,688 of 2,272)** but not the highest disclosed total per
project — Solicitor General's 8 projects (correctional facilities) and Attorney General's 31 (courthouses)
average far higher disclosed budgets each, consistent with the kind of large single-site capital builds those
ministries undertake.
