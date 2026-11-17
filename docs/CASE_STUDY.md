# Portfolio Case Study: Ontario Infrastructure Decision Intelligence Platform

## The problem

In 2024, as part of a university group project, I worked with four collaborators to analyze a static CSV
snapshot of Ontario's public infrastructure disclosure data using PostgreSQL and SQL. It was a solid first
pass — a working database, ten analysis queries, a written report — but it had the weaknesses typical of a
first analytics project: unknown financial values coalesced to `0`, text nulls replaced with the string
`'unknown'`, no automated data quality checks, and a `DATE` column type applied to a field that, it turns
out, almost never actually contains a full date.

Revisiting it in 2026, the goal was to rebuild it as a credible analytics engineering artifact: a
reproducible pipeline against the **live** government source (not a frozen CSV), a defensible dimensional
model, automated data quality checks with real results, and an interactive application that supports
decisions without overclaiming what the data can prove.

## What I actually found when I re-audited the live source

Before writing any code, I queried Ontario's own CKAN API directly rather than assuming the old project's
README link still worked or described the data correctly. It did still work — the resource is active, 2,272
rows as of this writing — but the content told a different story than expected:

- **47% of all projects report a literal $0 budget.** Not missing — a real `0` in a `NUMERIC` field. The
  2024 project's `COALESCE(budget, 0)` pattern, applied in reverse, would have made this indistinguishable
  from genuine missing data. This became the single most important modeling decision in the rebuild: budgets
  are never coalesced, and a `budget_undisclosed` flag exists specifically to make this ambiguity visible
  instead of hidden.
- **96% of target completion dates have no day-level precision** — "Dec-23", not "2023-12-15." A `DATE`
  column forcing day precision onto this data would either fail to load or silently invent a day that was
  never in the source. I built a precision-aware date model instead (`target_completion_precision` +
  `target_completion_upper_bound`) that's honest about exactly how much the source actually tells us.
- **One date is literally impossible** — "6/31/2026" (June has 30 days) — caught automatically by the
  pipeline's validation, not found by manual inspection.
- **The `Highway / Transit Line` field is empty for all 2,272 current rows**, meaning one of the original
  project's ten analysis queries would silently return zero rows today — a concrete example of why "verify
  the schema before building the pipeline" (the brief's explicit instruction) mattered in practice, not just
  in principle.
- **Funding-source fields are disclosure flags, not dollar amounts.** The original schema typed them as
  `VARCHAR`, which was the right instinct for the wrong reason — I confirmed from Ontario's own field
  documentation that these columns only ever contain `"Yes"` or blank, never a number or `"No"`.

Full detail: [`docs/AUDIT.md`](AUDIT.md).

## What I built

A five-stage pipeline (Source → Ingestion → Validation → Transformation → Database), a 5-table dimensional
Postgres schema, a FastAPI analytical layer, and a React/TypeScript dashboard with four views: an overview,
an interactive Leaflet map, a searchable/sortable/exportable project table, and a "Decision Intelligence"
page that answers specific investment and data-completeness questions with SQL-traceable numbers.

Every transformation decision is a named, independently tested pure function (`pipeline/ont_pipeline/transform.py`,
33 passing unit tests) rather than inline SQL `UPDATE` statements, which makes the reasoning behind each
decision reviewable and testable in a way the original project's cleaning script wasn't.

## Findings from the current data (see [`docs/SQL_EXAMPLES.md`](SQL_EXAMPLES.md) for every query and its real output)

- **Central region has the largest disclosed infrastructure investment** ($4.38B across 483 projects), but
  Northeast has the *most* projects (488) and the *smallest* disclosed total — driven substantially by a 53%
  budget non-disclosure rate there, the highest of any region. This is as much a data-completeness story as
  an investment-distribution one.
- **Infrastructure ministry runs by far the most projects (1,688 of 2,272)**, but Solicitor General (8
  projects, almost entirely large correctional facilities) and Attorney General (31 projects, mostly
  courthouses) have far higher *average* disclosed budgets per project — consistent with the kind of large,
  single-site capital builds those ministries undertake.
- **50 projects have a passed target completion window and are not yet marked Complete** (42 "Under
  construction," 8 "Planning"). This is the honest, narrow version of "which projects might need a status
  check-in" — not a claim that any of them are delayed, since the dataset's date precision alone can't
  support that claim, and the vast majority of projects that pass their target window do eventually
  complete (1,864 of 1,873 Complete projects show this pattern).

## Limitations

- **No stable project ID in the source.** The pipeline's idempotency (verified: a second run against
  unchanged data inserts 0 new rows) relies on a content hash. If a future snapshot changes one field of an
  existing project (e.g. its status), the pipeline will currently treat it as a new row rather than an
  update to a tracked project, since there's no reliable way to know it's "the same" project without a
  government-issued ID. Tracking a single project's status changes over time across snapshots is explicitly
  out of scope for this version.
- **$0 budgets are *probably* "undisclosed," not confirmed.** I can't rule out that a handful are genuinely
  $0-cost initiatives. The flag exists to make this visible for a human to judge, not to assert certainty.
- **Funding-source booleans indicate disclosure, not a dollar amount or percentage.** Any dashboard claim
  about "funding mix" is necessarily about *how many* projects disclosed each source, never *how much* came
  from each.
- **"Target window passed" is a forecast-precision limitation of the source, not a performance measurement.**
  It is never presented in this project as evidence of delay.

## Decisions this system supports

- Where to prioritize a status-update follow-up (the 50 past-window, not-complete projects) — a data-backed
  starting point for a conversation, not an automated verdict.
- Where regional investment appears concentrated or where budget non-disclosure is high enough to caveat any
  investment comparison for that region.
- Which ministries run the most projects vs. which run the highest average-budget projects — a useful
  distinction for anyone assuming "most projects" and "most investment" are the same thing.

## What I'd build next

A live-model comparison in the eval sense isn't applicable here (there's no AI model in this pipeline), but
the natural next steps are: tracking project identity across snapshots (would need either a stable source ID
or a carefully validated fuzzy-matching approach, explicitly out of scope here because getting it wrong would
be worse than not having it), a scheduled re-ingestion job instead of manual runs, and a Postgres-backed
deployment target for a persistent hosted demo (documented but not set up in this version — see the README's
Deployment section).
