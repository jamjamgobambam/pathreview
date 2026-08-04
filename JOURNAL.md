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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md steps 1-2: `api/routes/health.py` now builds the Redis client
with `redis.Redis.from_url(settings.redis_url, decode_responses=True)` instead of the nonexistent
`settings.redis_host`/`settings.redis_port`. Completed step 3 by rewriting `tests/unit/test_health.py`
to call `health_check()` directly with a mocked DB session, covering both the "healthy" (ping
succeeds) and "unhealthy" (ping raises, 503) cases, and retired the Week 8 reproduction test that
asserted the bug (step 5), keeping only the test that documents `Settings` never defines
`redis_host`/`redis_port`. Also completed step 4 (manual verification): started a local
`redis-server`, called `health_check()` directly, and confirmed it reports `"healthy"`; stopped
Redis and confirmed it correctly flips to `"unhealthy"`/503.

**Next steps:**
Open the PR as a draft, request peer/mentor review per the course Slack channel, and address any
feedback before marking it ready for review.

**Blockers:**
The repo's pre-commit hook (ruff + mypy) fails on pre-existing type/lint issues in `health.py`
that exist on `main` and are unrelated to this fix (untyped `health_check` signature, `Depends()`
in default args, an untyped `health_status` dict) — confirmed via `git stash` that these predate
this branch. Skipped the hook for this one commit and documented the pre-existing counts in the
PR description rather than expanding scope into a full retype of the file.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/326

**Branch:** `fix/155-redis-health-check`

**What you built:**
Fixed the `/health` endpoint's Redis probe, which referenced `settings.redis_host`/`settings.redis_port`
(fields that don't exist on `Settings`) and silently reported Redis as unconditionally unhealthy.
The probe now builds its client from the existing `settings.redis_url` via `redis.Redis.from_url(...)`,
so the health check reflects Redis's real status instead of always failing.

**Tests added or updated:**
`tests/unit/test_health.py` — kept `test_settings_has_no_redis_host_field` (documents the root
cause), and replaced the old reproduction tests with `test_health_check_reports_redis_healthy_when_ping_succeeds`
(calls `health_check()` with a mocked DB session and a mocked `redis.Redis.from_url`/`ping()` that
succeeds, asserting `dependencies.redis == "healthy"` and that the client was built from
`redis_url`) and `test_health_check_reports_redis_unhealthy_when_ping_fails` (mocks `ping()` to
raise `ConnectionError`, asserting `health_check()` raises a 503 `HTTPException` with
`dependencies.redis == "unhealthy"`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(`make test-unit`: 378 passed, 53 pre-existing failures unrelated to this issue, confirmed via
`git stash` to predate this branch. `make check`/lint: 182 pre-existing errors on `main`, still 182
after this change — net zero new issues; my changed lines are individually clean. `make check`/typecheck:
this change reduces `health.py`'s mypy error count from 11 to 8 by removing the `redis_host`/`redis_port`
attr-defined errors; the remaining 8 are pre-existing and unrelated to #155. Full details and the
pre-existing baseline comparison are documented in the PR description.)_

**Draft PR feedback received from:** none yet — just opened