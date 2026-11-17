# Ontario Infrastructure Decision Intelligence Platform

A reproducible data engineering, analytics, and BI platform built on Ontario's public infrastructure
disclosure data — rebuilt from a 2024 university group project into a portfolio-quality analytics
engineering project: a Python ingestion pipeline, a PostgreSQL dimensional model, automated data quality
checks with real results, a FastAPI analytical layer, and a React + TypeScript decision-intelligence
dashboard.

![Overview dashboard](docs/screenshots/overview.png)

## What this is, in one paragraph

Ontario publishes a live, public CSV of key infrastructure projects (courthouses, correctional facilities,
affordable housing, water infrastructure, and more) through its open data portal. This project ingests that
data directly from the government's own API (not a static download), models it properly, runs eight
automated data quality checks against it, and serves it through a dashboard built to answer specific,
defensible questions — what's being built, where, by which ministry, and where the available data is simply
incomplete — without ever treating a `$0` budget as free, a missing status update as proof of delay, or a
passed forecast window as a confirmed problem.

## Original project and what changed

This started as a 2024 group project by **Tobi Oladimeji, Sushma Gouri Deivanayagam, Sachin Suresh, Dwij
Shyamsunder, and Surya Amit Malwade** — a PostgreSQL + SQL analysis of a static dataset snapshot. That work
is fully preserved, unedited, at [`docs/original-2024/`](docs/original-2024/).

The 2026 rebuild is new, independent work: a full repository and live-source audit
([`docs/AUDIT.md`](docs/AUDIT.md)), a from-scratch Python pipeline, a new dimensional schema, an automated
data-quality framework, a FastAPI service, and the React dashboard. See the Audit doc for the specific
weaknesses found in the original data cleaning (budget-to-zero coalescing, text-to-`'unknown'` coalescing,
full-row-only duplicate detection, a `DATE` type applied to a field that's almost never a real date) and
exactly how each was addressed.

## Screenshots

| Overview | Map |
|---|---|
| ![Overview](docs/screenshots/overview.png) | ![Map](docs/screenshots/map.png) |

| Projects | Decision Intelligence |
|---|---|
| ![Projects](docs/screenshots/projects.png) | ![Insights](docs/screenshots/insights.png) |

| Project detail | Mobile |
|---|---|
| ![Detail](docs/screenshots/project-detail.png) | ![Mobile](docs/screenshots/overview-mobile.png) |

All screenshots are from a real run of this app against live-ingested data (2,272 projects, ingested
2026-11-15) — not mockups.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full diagram and stack rationale. In short:

```
Ontario CKAN API → pipeline/ (Python: fetch, validate, transform, load, quality-check)
                 → PostgreSQL (dimensional schema, see docs/ERD.md)
                 → api/ (FastAPI, read-only analytical endpoints)
                 → web/ (React + TypeScript dashboard)
```

## Reproducing this locally

### Prerequisites
- Docker and Docker Compose (for PostgreSQL)
- Python 3.11+
- Node 18+

### 1. Start the database

```bash
cp .env.example .env
docker compose up -d db
```

This starts PostgreSQL and automatically runs everything in `db/migrations/` on first boot (via Postgres's
own `docker-entrypoint-initdb.d` convention) — the database is created from scratch with no manual migration
step.

> **Note on how this was verified:** this sandbox environment doesn't have a Docker daemon available, so I
> verified the full pipeline → database → API → web flow against a locally-installed PostgreSQL 16 instance
> with the exact same `db/migrations/*.sql` files applied by hand, rather than through `docker compose up`
> itself. The Compose file's configuration (same Postgres version family, same migration mount, same
> environment variables) mirrors what I tested, but I have not personally run `docker compose up` end to end
> in this project. Please verify it works for you and open an issue if it doesn't.

### 2. Run the pipeline

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://ont_app:ont_dev_password@localhost:5432/ont_infrastructure"
python -m ont_pipeline.run_pipeline
```

This downloads the current live source, saves a dated raw snapshot + metadata under `data/raw/`, transforms
and loads it into Postgres (idempotently — re-running inserts 0 additional rows), runs all 8 data quality
checks, and writes `data/quality_reports/latest.md`. **Real output from an actual run:**

```
[1/5] Fetching current source snapshot from https://data.ontario.ca/api/3/action ...
      Resource: 'Ontario Builds: Communities', 2272 rows, md5=7ebcf40da7a93cd9b46c5e10893ea8c1
[2/5] Transforming 2272 rows ...
      1 row-level warnings recorded (see quality report)
[3/5] Loading into Postgres (idempotent upsert) ...
      Batch 1: 2272 new rows inserted, 0 already present (idempotent), 1 row warnings
[4/5] Running automated data quality checks ...
      [OK ] required_fields_present: 0/2272 (critical)
      [OK ] structural_duplicates: 0/2272 (critical)
      [FAIL] target_completion_date_validity: 1/2272 (warning)
      [OK ] coordinate_validity: 0/2272 (warning)
      [OK ] unexpected_status_values: 0/2272 (warning)
      [OK ] financial_anomalies: 0/2272 (critical)
      [OK ] referential_integrity: 0/2272 (critical)
      [OK ] source_schema_drift: 0/21 (warning)
Pipeline completed successfully.
```

Re-run it again to see the idempotency guarantee for yourself — it will report `0 new rows inserted, 2272
already present`.

### 3. Run the API

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://ont_app:ont_dev_password@localhost:5432/ont_infrastructure"
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation (FastAPI's automatic OpenAPI UI).

### 4. Run the web app

```bash
cd web
npm install
npm run dev
```

Visit `http://localhost:5173`.

## Running the tests

```bash
# Pipeline: 33 unit tests (date/coordinate/budget/funding parsing, row hashing)
cd pipeline && source .venv/bin/activate && python -m pytest tests/ -v

# API: 13 integration tests against a running database (run the pipeline first)
cd api && source .venv/bin/activate && python -m pytest tests/ -v

# Web: 16 component/unit tests
cd web && npm test
```

**Actual results from this project's own test runs:** 33/33 pipeline tests pass, 13/13 API tests pass,
16/16 web tests pass — 62 tests total. `npm run build` and `npm run lint` / `tsc --noEmit` also pass cleanly
on the web app; `python -m pytest`, lint, and build all pass on the pipeline and API.

## Documentation

- [`docs/AUDIT.md`](docs/AUDIT.md) — the full repository and live-source audit that preceded this rebuild
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system diagram and stack rationale
- [`docs/ERD.md`](docs/ERD.md) — entity-relationship diagram
- [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) — every column, defined
- [`docs/SQL_EXAMPLES.md`](docs/SQL_EXAMPLES.md) — real queries with real, captured output
- [`docs/DATA_QUALITY_REPORT.md`](docs/DATA_QUALITY_REPORT.md) — a committed snapshot of real pipeline output
- [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) — the portfolio case study: problem, findings, limitations
- [`docs/original-2024/`](docs/original-2024/) — the original, preserved 2024 project

## Deployment

This project is designed to run locally; it was not deployed to any hosted environment as part of this
rebuild, per the project's own working instructions ("do not merge, deploy, or incur costs without
approval"). If you want to deploy it:

- **Database**: any managed Postgres works (a free tier like [Neon](https://neon.tech) or
  [Supabase](https://supabase.com) is sufficient at this data size — 2,272 rows). Run the files in
  `db/migrations/` against it once.
- **API**: the `api/Dockerfile` builds a standard container; deploy it anywhere that runs a Docker image
  (Render, Fly.io, Railway's free tiers all work) with `DATABASE_URL` and `API_CORS_ORIGINS` set.
- **Web**: `npm run build` produces a static `web/dist/` — deployable to any static host (Netlify, Vercel,
  Cloudflare Pages, GitHub Pages) with `VITE_API_BASE_URL` set at build time to your deployed API's URL.
- **Pipeline**: intended to be run on a schedule (e.g. a daily cron job or scheduled GitHub Action) hitting
  the same `DATABASE_URL` as the deployed API.

## Technical trade-offs

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#why-this-stack) for the full reasoning. The short version:
plain SQL migrations over an ORM/migration framework (small, stable schema), FastAPI + psycopg2 over an ORM
(read-only analytical queries don't benefit from one), Leaflet/OpenStreetMap over a paid maps API, and the
frontend runs via `npm run dev` rather than in Docker (faster iteration; Postgres is the piece that actually
needs environment parity).

## Limitations

See [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md#limitations) for the full list. The most important ones: the
source provides no stable project ID, so the pipeline's idempotency is based on exact content matching, not
true project identity tracking across snapshots; `$0` budgets are flagged as likely-undisclosed but not
confirmed; funding-source fields indicate disclosure, not dollar amounts; and "target window passed" is
never presented as evidence of delay.

## License

[MIT](LICENSE), originally applied by Tobi Oladimeji for the 2024 project and carried forward.
