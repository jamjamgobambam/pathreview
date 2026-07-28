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
