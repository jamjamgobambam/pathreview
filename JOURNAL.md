# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's PostgreSQL probe in `api/routes/health.py` runs
`await db.execute("SELECT 1")`, passing the query as a bare Python string.
SQLAlchemy 2.x no longer accepts raw textual statements and raises an
`ArgumentError` telling you to wrap them in `text()`. Because the health
handler catches that exception, Postgres gets reported as `unhealthy` and the
endpoint returns a 503 even when the database is actually up and reachable — a
false-negative outage. A successful fix wraps the query with
`sqlalchemy.text()` (`db.execute(text("SELECT 1"))`) so the probe runs, the
endpoint reports accurate database status, and monitoring stops firing on a
healthy DB. The change is confined to the API module's health route and its
accompanying unit test.

**Branch name:** fix/154-health-check-sql-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" reasoning

- **Scope is tiny and localized.** The fix is one import plus one line in a
  single file (`api/routes/health.py`), plus a unit test — no sprawling change.
- **No cross-module knowledge required.** It lives entirely in the API module;
  I don't need to understand the RAG, agent, or ingestion pipelines to fix it.
- **Well-defined bug with a standard, known fix.** SQLAlchemy 2.x's `text()`
  requirement is documented behavior, so there's little ambiguity about the
  correct solution.
- **Reproducible and testable without secrets.** It can be exercised via a unit
  test against a DB session and doesn't depend on the `OPENROUTER_API_KEY` or
  any external AI service.
- **Correct difficulty match.** Labeled `good first issue` + `tier-1`, which
  fits a first contribution to a large codebase.

**Reproduction confirmed locally:** With the stack running, `GET
http://localhost:8000/health` returns HTTP 503 with `postgres: "unhealthy"`,
even though PostgreSQL is up (seeding connected successfully and the Docker
container reports healthy). The handler in `api/routes/health.py` catches the
SQLAlchemy 2.x `ArgumentError` from the unwrapped `SELECT 1` and mislabels the
database as down — exactly the behavior described in the issue.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/p-disha/pathreview/commit/0f4619152141b1806092c640b65e8ca2651564ed

**Reproduction summary:**
With the full stack running locally, I called `GET
http://localhost:8000/health` and observed **HTTP 503** with
`postgres: "unhealthy"` even though PostgreSQL was up — seeding had just
connected to it and the Docker `db` container reported healthy. The bare
`SELECT 1` string raises SQLAlchemy 2.x's `ArgumentError`, which the handler's
broad `except` swallows and mislabels the DB as down. The commit above records
these steps in `JOURNAL.md`; the regression-guard unit test in
`tests/unit/test_health.py` (commit `aca8cf0`) captures the same behavior as a
test that fails on the raw string and passes once it is wrapped in `text()`.

**PLAN.md link:** https://github.com/p-disha/pathreview/blob/fix/154-health-check-sql-text/PLAN.md

**Walkthrough video (recommended):** _(optional — not recorded)_

**Blockers or open questions:**
The handler's broad `except Exception` also masks the sibling Redis bug (#155,
`settings.redis_host`) in the same file, so `/health` still returns 503 overall
until #155 is fixed even though postgres now reads healthy. Open question for
mentors: is a #154-only PR (postgres healthy, redis still failing) the expected
scope, or should the redis fix be bundled?
