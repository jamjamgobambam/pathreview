## Week 7 — Issue selection

**Issue link:** [#155](https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report the status of Postgres, Redis, and the
vector DB, but its Redis probe reads `settings.redis_host` and `settings.redis_port` in
`api/routes/health.py`, and neither field is defined on the `Settings` model in
`core/config.py` — only a single `redis_url` field exists. This raises an `AttributeError`
on every call, which is swallowed by the surrounding `try/except`, so Redis is always
reported `unhealthy` and the endpoint returns a 503 even when Redis is actually up. A
successful fix updates the probe to build the Redis client from `settings.redis_url` so
the health check accurately reflects Redis's real status.

**Branch name:** `fix/155-redis-health-check`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [c7ad417 — test: reproduce issue #155 - redis_host AttributeError in health check](https://github.com/rushilshah11/pathreview/commit/c7ad417)

**Reproduction summary:**
Confirmed the root cause with `grep -rn "redis_host\|redis_port" core api`: `api/routes/health.py`
(lines 45-46) reads `settings.redis_host`/`settings.redis_port`, but `Settings` in `core/config.py`
only defines `redis_url`. Instantiating `Settings()` and accessing `.redis_host` raises
`AttributeError: 'Settings' object has no attribute 'redis_host'`. Running the exact try/except
block from `health.py` shows this error is caught silently, so Redis is unconditionally reported
`"unhealthy"` (and the endpoint returns 503) regardless of Redis's real status. Added
`tests/unit/test_health.py` with two tests that reproduce this (`pytest tests/unit/test_health.py -v`
passes, documenting the current broken behavior).

**PLAN.md link:** [PLAN.md](../../blob/fix/155-redis-health-check/PLAN.md)

**Walkthrough video (recommended):** _not recorded this week_

**Blockers or open questions:**
The app's startup lifespan requires a reachable Postgres, so I couldn't boot `uvicorn` locally
without a running Postgres instance to hit `GET /health` directly end-to-end. Reproduced the bug
at the `Settings`/`health.py` code-path level instead (see PLAN.md "Risks & unknowns" for the
plan to add a proper `TestClient`-based test in Week 9).