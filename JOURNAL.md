## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` checks Postgres connectivity by calling
`db.execute("SELECT 1")` with a plain Python string. SQLAlchemy 2.x no longer accepts raw
strings for textual SQL — they must be wrapped in `sqlalchemy.text()` — so the call raises
an `ArgumentError` instead of running the query. Because that exception is caught by the
surrounding `try/except`, the health check reports Postgres (and the overall service) as
unhealthy even when the database is up and reachable. A correct fix wraps the query string
in `text("SELECT 1")` so the probe actually executes and reflects the real DB status.

**Scope reasoning ("Is this right for me?"):**
Worked through the issue-selection checklist and confirmed this is a well-sized Tier 1 pick:

- **Appropriately scoped / bounded blast radius:** The fix is a single line in a single file
  (`api/routes/health.py:31`) — wrapping the existing `"SELECT 1"` string in `text(...)`. No
  schema changes, no migrations, no API-contract changes, and no new dependencies (`text` already
  ships with the SQLAlchemy version in use).
- **Well-understood root cause:** The failure mode is a known SQLAlchemy 2.x behavior change
  (raw strings are no longer accepted for textual SQL), so there is no open-ended investigation.
- **Clear, deterministic acceptance criteria:** With the DB up, `/health` should report Postgres
  (and overall status) as healthy instead of catching an `ArgumentError`. This is directly
  observable and testable via the existing `/health` endpoint.
- **Fits my skill level and available time:** Self-contained, isolated to the health probe's
  `try/except`, with no cross-subsystem coordination — completable within the Week 7 window.

This is why it maps to Tier 1 rather than a larger tier.

**Branch name:** fix/154-health-check-textual-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sr-daniels/pathreview/commit/ff3d092aa82a4a02d189834f80c94d4f1f1338db

**Reproduction summary:**
Added a unit test that exercises the health check's Postgres probe with a mocked async session; confirmed db.execute("SELECT 1") raises sqlalchemy.exc.ArgumentError under SQLAlchemy 2.x, which the route's try/except catches and misreports as "postgres": "unhealthy".

**PLAN.md link:** https://github.com/sr-daniels/pathreview/blob/fix/154-health-check-textual-sql/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in api/routes/health.py (wrapped the raw SQL string in sqlalchemy.text()) and updated tests/unit/test_health.py to assert the health check now reports postgres as healthy. All sub-tasks from PLAN.md's core fix are done; ran make check and make test-unit with no new failures introduced versus baseline.

**Next steps:**
Open a draft PR and request peer/mentor review. The live-DB smoke test (confirming GET /health reports postgres "healthy" against a running database via docker compose up) is still **pending** — see Blockers.

**Verification status:**
- Fix verified at the unit level: tests/unit/test_health.py confirms the postgres probe now reports "healthy" (and that the query is a text() clause, not a raw string), plus a regression that a genuine DB error still reports "unhealthy". make test-unit shows no new failures vs. baseline.
- Live-DB manual smoke test: **pending / not yet run** (blocked, see below).

**Blockers:**
- **Live-DB check blocked — Docker will not run locally.** Docker Desktop is installed but its daemon does not become ready when launched, and the `docker` / `docker compose` command-line tools are not operational in this environment (commands hang / the CLI is unavailable). Because docker compose can't bring up Postgres, the live GET /health smoke test could not be performed. It remains pending until Docker is working (or the check is run on another machine). This does not affect the code fix, which is covered by the unit tests above.
- Out-of-scope discovery: the /health redis probe reads settings.redis_host / settings.redis_port, which aren't defined on Settings, so redis always reports unhealthy independent of #154 — noted in PLAN.md as a follow-up.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/894

**Branch:** fix/154-health-check-textual-sql

**What was built:**
Fixed the /health endpoint's Postgres probe, which passed a raw SQL string to db.execute() and raised sqlalchemy.exc.ArgumentError under SQLAlchemy 2.x — causing Postgres to be misreported as "unhealthy" even when the database was up. The fix wraps the query in sqlalchemy.text("SELECT 1") in api/routes/health.py, so the probe runs and reflects real connectivity.

**Tests:**
Updated `tests/unit/test_health.py` with two tests: `test_health_check_reports_postgres_healthy_when_query_succeeds` — asserts the probe reports `dependencies.postgres == "healthy"` once the query succeeds, and guards against regression by asserting the executed statement is a SQLAlchemy `text()` clause rather than a raw `str`; and `test_health_check_reports_postgres_unhealthy_on_real_db_error` — asserts a genuine DB connection error is still reported as "unhealthy" (HTTP 503), so the fix doesn't mask real outages.

**Self-review:**
- [x] `make test-unit` — this change introduces **no new failures**: identical `53 failed / 377 passed` before and after (the 53 are pre-existing and unrelated to /health; baseline captured before any change), and the two updated test_health.py tests pass.
- [x] `make check` — this change introduces **no new lint/type errors**: both changed files are clean under `black`, add zero new `ruff` errors (repo total actually dropped 183 → 182), and `mypy` output is byte-for-byte identical to baseline. (The repo has pre-existing ruff/mypy debt unrelated to #154, left untouched to keep the diff minimal.)
