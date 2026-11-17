# Entity-Relationship Diagram

Replaces the original hand-drawn ERD (preserved at
[`docs/original-2024/pictures/ONT_ERD.png`](original-2024/pictures/ONT_ERD.png)) with the actual schema in
[`db/migrations/001_schema.sql`](../db/migrations/001_schema.sql). See
[`docs/DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for column-level definitions.

```mermaid
erDiagram
    DIM_REGION ||--o{ FACT_PROJECT : "categorizes"
    DIM_COMMUNITY ||--o{ FACT_PROJECT : "categorizes"
    DIM_MINISTRY ||--o{ FACT_PROJECT : "categorizes"
    DIM_STATUS ||--|{ FACT_PROJECT : "categorizes"
    INGESTION_BATCH ||--|{ FACT_PROJECT : "loaded by"
    INGESTION_BATCH ||--o{ DQ_CHECK_RUN : "checked by"

    DIM_REGION {
        serial region_id PK
        text region_name UK
    }
    DIM_COMMUNITY {
        serial community_id PK
        text community_name UK
    }
    DIM_MINISTRY {
        serial ministry_id PK
        text ministry_name UK
    }
    DIM_STATUS {
        serial status_id PK
        text status_name UK
    }
    INGESTION_BATCH {
        serial batch_id PK
        text source_url
        text source_resource_id
        timestamptz retrieved_at
        text source_last_modified
        text source_file_hash
        int source_row_count
    }
    FACT_PROJECT {
        serial project_id PK
        text source_row_hash UK
        int batch_id FK
        text project_name
        text category
        text area
        int community_id FK "nullable"
        int region_id FK "nullable"
        int ministry_id FK "nullable"
        int status_id FK
        text address
        text postal_code
        numeric latitude "nullable"
        numeric longitude "nullable"
        text coordinate_status
        text multi_point_raw "nullable"
        text target_completion_date_raw
        text target_completion_precision
        date target_completion_upper_bound "nullable"
        numeric estimated_total_budget
        boolean budget_undisclosed
        boolean municipal_funded
        boolean provincial_funded
        boolean federal_funded
        boolean other_funded
    }
    DQ_CHECK_RUN {
        serial run_id PK
        int batch_id FK
        text check_name
        text severity
        text status
        int affected_count
        int total_count
        jsonb details
    }
```

## Design decisions this encodes

- **`fact_project` is the grain of one project record from the source.** There is no project-level history
  table — the source provides no stable ID across snapshots, so a re-ingested update to an existing project
  is a modeling limitation documented in the README, not silently hidden here.
- **`region_id`, `community_id`, and `ministry_id` are nullable foreign keys** — reflecting that ~3% of
  source rows genuinely don't specify a community or region. A `NOT NULL` constraint here would have forced
  either inventing a fake dimension row or silently dropping real records.
- **`area` is a plain column on `fact_project`, not a dimension**, because the audit found 2 communities with
  inconsistent area values in the live source — forcing it into a `dim_area` table would require picking one
  value and hiding the inconsistency.
- **`v_project` (not shown above — see [`db/migrations/002_views.sql`](../db/migrations/002_views.sql)) is a
  plain `JOIN`, not a materialized view** — the dataset is small enough (2,272 rows) that a live join costs
  nothing, and a plain view guarantees the API never serves stale data after a pipeline run.
