-- Ontario Infrastructure Decision Intelligence Platform — schema
--
-- Design notes (see docs/AUDIT.md for the evidence behind each decision):
--   * Funding fields are BOOLEAN disclosure flags, not amounts — the source
--     only ever contains "Yes" or blank for Municipal/Provincial/Federal/
--     Other Funding. Modeling them as money would invent data.
--   * estimated_total_budget is NEVER coalesced to 0. The source itself uses
--     a literal 0 for ~47% of rows, almost certainly meaning "not yet
--     disclosed" rather than "costs nothing" — budget_undisclosed flags this
--     without destroying or hiding the raw source value.
--   * target_completion_date_raw preserves exactly what the source said
--     ("Dec-23", "To Be Determined", "2026", or a full date). Because >95%
--     of real values have no day-level precision, target_completion_date is
--     NOT a single trustworthy DATE — see target_completion_precision and
--     target_completion_upper_bound below.
--   * coordinate_status distinguishes "no coordinates provided" from "this
--     is a linear/multi-site project with more than one coordinate," which
--     the source encodes as a pipe-delimited list in a single cell. Neither
--     case is collapsed into a single invented point.

CREATE TABLE IF NOT EXISTS dim_region (
    region_id   SERIAL PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_community (
    community_id   SERIAL PRIMARY KEY,
    community_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_ministry (
    ministry_id   SERIAL PRIMARY KEY,
    ministry_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_status (
    status_id   SERIAL PRIMARY KEY,
    status_name TEXT NOT NULL UNIQUE
);

-- One row per pipeline run that successfully loaded data. Answers
-- "where did this number come from and when" for every fact row.
CREATE TABLE IF NOT EXISTS ingestion_batch (
    batch_id             SERIAL PRIMARY KEY,
    source_url           TEXT NOT NULL,
    source_resource_id   TEXT NOT NULL,
    retrieved_at         TIMESTAMPTZ NOT NULL,
    source_last_modified TEXT,
    source_file_hash     TEXT NOT NULL,
    source_row_count     INTEGER NOT NULL,
    notes                TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_project (
    project_id      SERIAL PRIMARY KEY,
    -- Deterministic hash of the full source row. The source provides no
    -- stable project ID, so this is the identity used for idempotent
    -- re-ingestion: re-running the pipeline against unchanged source data
    -- inserts zero new rows. See docs/AUDIT.md "Duplicates" and the README
    -- Limitations section for what this does and doesn't catch.
    source_row_hash TEXT NOT NULL UNIQUE,
    batch_id        INTEGER NOT NULL REFERENCES ingestion_batch(batch_id),

    project_name TEXT NOT NULL,
    description  TEXT,
    result       TEXT,

    category TEXT NOT NULL DEFAULT 'Communities',

    area         TEXT,
    community_id INTEGER REFERENCES dim_community(community_id),
    region_id    INTEGER REFERENCES dim_region(region_id),
    ministry_id  INTEGER REFERENCES dim_ministry(ministry_id),
    status_id    INTEGER NOT NULL REFERENCES dim_status(status_id),

    address     TEXT,
    postal_code TEXT,

    latitude          NUMERIC(10, 6),
    longitude         NUMERIC(10, 6),
    coordinate_status TEXT NOT NULL DEFAULT 'missing'
        CHECK (coordinate_status IN ('single_point', 'multi_point', 'missing')),
    multi_point_raw   TEXT, -- original pipe-delimited lat/long lists, preserved verbatim

    highway_transit_line TEXT,

    target_completion_date_raw    TEXT NOT NULL,
    target_completion_precision   TEXT NOT NULL DEFAULT 'unknown'
        CHECK (target_completion_precision IN ('day', 'month', 'year', 'unknown', 'invalid')),
    -- The latest date consistent with the source's stated precision (e.g. for
    -- "Dec-23" this is 2023-12-31). Used for a defensible, conservative
    -- "target window has passed" check — never treated as a confirmed delay.
    target_completion_upper_bound DATE,

    estimated_total_budget NUMERIC(14, 2) NOT NULL,
    -- True when estimated_total_budget = 0. The raw value is preserved
    -- unchanged; this flag only marks it as needing cautious interpretation.
    budget_undisclosed BOOLEAN NOT NULL DEFAULT FALSE,

    -- "Indicates whether X dollars were allocated on the ministry's
    -- disclosure" (Ontario's own field description) — a disclosure flag,
    -- not a dollar amount, and not a confirmed "no" when false/null.
    municipal_funded  BOOLEAN,
    provincial_funded BOOLEAN,
    federal_funded    BOOLEAN,
    other_funded      BOOLEAN,

    website TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_project_community ON fact_project(community_id);
CREATE INDEX IF NOT EXISTS idx_fact_project_region ON fact_project(region_id);
CREATE INDEX IF NOT EXISTS idx_fact_project_ministry ON fact_project(ministry_id);
CREATE INDEX IF NOT EXISTS idx_fact_project_status ON fact_project(status_id);
CREATE INDEX IF NOT EXISTS idx_fact_project_coord_status ON fact_project(coordinate_status);
CREATE INDEX IF NOT EXISTS idx_fact_project_target_upper ON fact_project(target_completion_upper_bound);
CREATE INDEX IF NOT EXISTS idx_fact_project_budget ON fact_project(estimated_total_budget);
CREATE INDEX IF NOT EXISTS idx_fact_project_batch ON fact_project(batch_id);

-- Results of each automated data-quality check, per pipeline run. This is
-- what docs/DATA_QUALITY_REPORT.md and the dashboard's Data Quality view
-- both read from — the same real numbers, not separately maintained copies.
CREATE TABLE IF NOT EXISTS dq_check_run (
    run_id         SERIAL PRIMARY KEY,
    batch_id       INTEGER NOT NULL REFERENCES ingestion_batch(batch_id),
    run_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    check_name     TEXT NOT NULL,
    severity       TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    status         TEXT NOT NULL CHECK (status IN ('pass', 'fail')),
    affected_count INTEGER NOT NULL DEFAULT 0,
    total_count    INTEGER NOT NULL DEFAULT 0,
    details        JSONB
);

CREATE INDEX IF NOT EXISTS idx_dq_check_run_batch ON dq_check_run(batch_id);
