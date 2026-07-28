# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint in `api/routes/health.py` probes the database by
executing the literal string `"SELECT 1"`. SQLAlchemy 2.x no longer accepts
raw strings for textual SQL — they must be wrapped in `sqlalchemy.text()` —
so the probe raises an `ArgumentError` instead of running the query. As a
result, `GET /health` reports the database as down even when it is perfectly
reachable, which makes the endpoint useless for monitoring and can trigger
false alarms or failed container health checks. A successful fix wraps the
probe query in `text("SELECT 1")` so the health check accurately reflects
real database connectivity, with a test covering the probe.

**"Is this right for me?" checklist reasoning:**
The scope is small and well-bounded: the bug is a single incorrect call in
one route file, the error message in the issue points directly at the fix,
and it doesn't require touching the schema, migrations, or other services.
It's a real correctness bug (not cosmetic), it's testable in isolation with
a unit test against the route handler, and it teaches the SQLAlchemy 1.x →
2.x API difference. That makes it a good Tier 1 fit — achievable in a few
hours with a clear definition of done.

**Branch name:** `fix/154-health-check-db-probe-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [fill in after committing — link to the commit adding `tests/unit/test_health_probe.py`]

**Reproduction summary:**
I reproduced the bug by running the app locally and hitting the health
endpoint with a fully working database: `curl -i http://localhost:8000/health`.
Even though Postgres was up and reachable, the endpoint returned
`503 Service Unavailable` with `"postgres": "unhealthy"` in the JSON body, and
the API logs showed `postgres_health_check_failed` with a SQLAlchemy
`ArgumentError` — the raw string `"SELECT 1"` on `api/routes/health.py:31` is
rejected by SQLAlchemy 2.x because textual SQL must be wrapped in `text()`. I
then captured this in a unit test (`tests/unit/test_health_probe.py`): one test
asserts the raw-string probe raises `ArgumentError`, and one asserts the
`text("SELECT 1")` form succeeds against a live in-memory session.

**PLAN.md link:** [link to PLAN.md in the repo root on this branch]

**Walkthrough video (recommended):**

**Blockers or open questions:**
The reproduction test uses a sync SQLite connection because the `ArgumentError`
comes from SQLAlchemy's statement coercion (identical sync/async) and
`aiosqlite` isn't installed. Open question for Week 9: add `aiosqlite` for a
true async route-level test, or mock the `get_db` dependency instead.
