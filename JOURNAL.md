## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint in `api/routes/health.py` is supposed to check whether the PostgreSQL database is reachable by running a simple `SELECT 1` query. However, the query is passed as a plain Python string directly to SQLAlchemy's `execute()` method. SQLAlchemy 2.x no longer accepts raw strings as SQL — it requires them to be wrapped with `sqlalchemy.text()`. As a result, the probe raises an `ArgumentError` which is caught silently, causing the health check to always report postgres as "unhealthy" even when the database is fully operational. The fix is to import `text` from `sqlalchemy` and wrap the query: `await db.execute(text("SELECT 1"))`.

**Branch name:** fix/154-health-check-sqlalchemy-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/meenakshi-sethi/pathreview/commit/d2670e0

**Reproduction summary:**
Ran the real stack locally (`docker compose up -d db redis vector-db` + `uvicorn api.main:app`) and hit `GET /health` with Postgres healthy and reachable — the endpoint still returned `503` with `dependencies.postgres: "unhealthy"`, and the server log showed the exact swallowed error: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`. I also added `tests/unit/test_health_check.py`, which isolates the same `ObjectNotExecutableError` against a plain SQLAlchemy engine and confirms `text("SELECT 1")` is the fix.

**PLAN.md link:** https://github.com/meenakshi-sethi/pathreview/blob/fix/154-health-check-sqlalchemy-text/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
While reproducing, I found a second, unrelated bug in the same endpoint: the Redis probe (`api/routes/health.py:44-46`) reads `settings.redis_host`/`settings.redis_port`, but `core/config.py` only defines `redis_url`, so it always throws `AttributeError` and reports Redis as unhealthy too. This means that even after fixing #154, `/health` will still return `503` overall — verification needs to check `dependencies.postgres` specifically, not the overall status. I've noted this in PLAN.md as a risk and plan to flag it as a separate follow-up issue rather than fixing it as part of #154.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all of PLAN.md's sub-tasks 1-4: fixed the probe in `api/routes/health.py` (added `from sqlalchemy import text`, changed `db.execute("SELECT 1")` to `db.execute(text("SELECT 1"))`), added three route-level regression tests to `tests/unit/test_health_check.py`, and verified the fix locally against the real stack (`docker compose up -d db` + `uvicorn api.main:app`) — `GET /health` now returns `dependencies.postgres: "healthy"` instead of always `"unhealthy"`. Also confirmed via `make test-unit`/`make check` that my change introduces no new lint, type, or test failures compared to the pre-existing baseline (ran both before and after my change to diff the failure lists).

**Next steps:**
Finalize the PR description (sub-task 5 — documenting the fix and flagging the separate Redis `redis_host`/`redis_port` bug as a follow-up rather than fixing it in scope), get peer/mentor feedback on the draft PR, and submit.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [PASTE PR LINK HERE AFTER OPENING — see docs/PR_DRAFT.md for the description to paste in]

**Branch:** `fix/154-health-check-sqlalchemy-text`

**What you built:**
Fixed the `GET /health` Postgres probe, which passed a raw SQL string to `AsyncSession.execute()` — rejected outright by SQLAlchemy 2.x with `ObjectNotExecutableError`, silently caught, so the endpoint always reported `postgres: "unhealthy"` regardless of actual DB state. The fix wraps the query in `sqlalchemy.text()`, matching the 2.x `Executable`-only `execute()` contract.

**Tests added or updated:**
`tests/unit/test_health_check.py` — added a `TestHealthCheckPostgresProbe` class with three tests that call `health_check()` directly with a mocked `AsyncSession` (same pattern as `tests/unit/test_review_service.py`): (1) asserts the query passed to `execute()` is a `TextClause` instance rather than a raw `str` — this is the assertion that actually fails against the pre-fix code, since a mock's `execute()` doesn't raise on a plain string the way a real engine does; (2) asserts `dependencies.postgres == "healthy"` when the mocked query succeeds; (3) asserts `dependencies.postgres == "unhealthy"` when `execute()` raises a connection error, confirming the fix doesn't change behavior for a genuinely-down database.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both noted relative to a documented pre-existing baseline — see PR description for the exact pre-existing failure counts I diffed against; my change introduces zero new lint/type/test failures. It does not resolve any pre-existing mypy errors — same 11 errors before and after, none on the line this fix touches.)*

**Draft PR feedback received from:** none yet
