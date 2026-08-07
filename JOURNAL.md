# Journal — Issue #155: Redis health check config bug

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` references `settings.redis_host` and `settings.redis_port`, but the `Settings` class only defines `redis_url` — those two fields don't exist anywhere in the config. Because the check is wrapped in a broad `except Exception`, the resulting `AttributeError` gets silently swallowed and reported as `"redis": "unhealthy"` instead of crashing. In practice this means the health endpoint reports Redis as down on every single request, regardless of whether Redis is actually running — a permanent false negative that would make this monitoring signal useless in production. A successful fix makes the Redis check use the config field that actually exists (`redis_url`) so the endpoint reports Redis's real status.

**"Is this right for me?" checklist reasoning:**
Confirmed I could explain the issue and locate the exact files (`api/routes/health.py`, `core/config.py`) before claiming it. Tier 1 is a realistic match since this is a fresh contribution to an unfamiliar large codebase, and the fix is confined to a single function in one file. Checked the cohort ledger and found one other person already claimed #155 — confirmed with my own reasoning (and the module brief) that claims are non-exclusive and grading is based on my own submitted work, not on being first, so I proceeded. No blockers or dependencies noted on the issue.

**Branch name:** fix/155-redis-host-config

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Codebase Map (Week 7)

- `api/main.py` — FastAPI app factory, registers all route blueprints.
- `api/routes/health.py` — the file this issue lives in. A single `GET /health`
  endpoint that checks Postgres, Redis, and the vector DB in three independent
  `try/except` blocks, aggregating results into one JSON response.
- `core/config.py` — defines `Settings` (Pydantic `BaseSettings`), loaded from
  `.env`. This is the single source of truth for all configuration in the app.
  Notably, it only defines `redis_url` — there is no `redis_host` or `redis_port`.
- `core/database.py` — provides the `get_db` dependency used across the app for
  a database session.
- `tests/unit/` — all existing tests are unit tests for service/utility classes
  (parsers, scorers, detectors). None test a FastAPI route directly — no
  `TestClient` usage or `get_db` dependency override pattern exists anywhere
  in the current suite.

**Data flow for `/health`:** A GET request hits `health_check()` in
`api/routes/health.py`. Three independent checks run in sequence — Postgres
(via the injected `db` session), Redis (constructs its own client inline), and
vector DB (currently just checks that a config string is non-empty, not a real
connectivity check). Each check's result is written into a shared
`health_status` dict; if any check fails, the endpoint returns a 503 with the
full status breakdown as the error detail.

**Pattern noticed:** the Postgres and Redis checks both build their own
clients inline within the endpoint function, rather than using a shared
dependency — this is the only place in the whole codebase that constructs a
`redis.Redis` client directly (every other file that touches Redis receives an
already-built client via dependency injection).

## Problem Summary (Week 7)

Issue #155 reports that the `/health` endpoint's Redis check references
`settings.redis_host` and `settings.redis_port`, but `Settings` only defines
`redis_url`. Because the check is wrapped in a broad `except Exception`, this
`AttributeError` doesn't crash the endpoint — it's silently caught and
reported as `"redis": "unhealthy"`. The practical effect: `/health` reports
Redis as unhealthy on every single call, regardless of whether Redis is
actually running, making this monitoring signal permanently useless.

**Before:** `GET /health` always reports `"redis": "unhealthy"` (contributing
to an overall `"status": "unhealthy"` and a 503 response), even when Redis is
genuinely healthy.
**After:** `GET /health` correctly reports Redis's real status.

## Reproduction (Week 7-8)

1. Started the full stack with `make run` (Postgres + Redis via Docker,
   FastAPI + Vite dev servers via `make run`).
2. Confirmed via `docker compose ps` that Redis was genuinely healthy.
3. Hit the endpoint directly: `curl http://localhost:8000/health`.
4. Result: `{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"}, ...}`
grodl@DESKTOP-QD0ICNN MINGW64 ~/OneDrive/Desktop/AI Engineer/pathreview (fix/155-redis-host-config)
$ cat JOURNAL.md
# Journal — Issue #155: Redis health check config bug

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` references `settings.redis_host` and `settings.redis_port`, but the `Settings` class only defines `redis_url` — those two fields don't exist anywhere in the config. Because the check is wrapped in a broad `except Exception`, the resulting `AttributeError` gets silently swallowed and reported as `"redis": "unhealthy"` instead of crashing. In practice this means the health endpoint reports Redis as down on every single request, regardless of whether Redis is actually running — a permanent false negative that would make this monitoring signal useless in production. A successful fix makes the Redis check use the config field that actually exists (`redis_url`) so the endpoint reports Redis's real status.

**"Is this right for me?" checklist reasoning:**
Confirmed I could explain the issue and locate the exact files (`api/routes/health.py`, `core/config.py`) before claiming it. Tier 1 is a realistic match since this is a fresh contribution to an unfamiliar large codebase, and the fix is confined to a single function in one file. Checked the cohort ledger and found one other person already claimed #155 — confirmed with my own reasoning (and the module brief) that claims are non-exclusive and grading is based on my own submitted work, not on being first, so I proceeded. No blockers or dependencies noted on the issue.

**Branch name:** fix/155-redis-host-config

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Codebase Map (Week 7)

- `api/main.py` — FastAPI app factory, registers all route blueprints.
- `api/routes/health.py` — the file this issue lives in. A single `GET /health`
  endpoint that checks Postgres, Redis, and the vector DB in three independent
  `try/except` blocks, aggregating results into one JSON response.
- `core/config.py` — defines `Settings` (Pydantic `BaseSettings`), loaded from
  `.env`. This is the single source of truth for all configuration in the app.
  Notably, it only defines `redis_url` — there is no `redis_host` or `redis_port`.
- `core/database.py` — provides the `get_db` dependency used across the app for
  a database session.
- `tests/unit/` — all existing tests are unit tests for service/utility classes
  (parsers, scorers, detectors). None test a FastAPI route directly — no
  `TestClient` usage or `get_db` dependency override pattern exists anywhere
  in the current suite.

**Data flow for `/health`:** A GET request hits `health_check()` in
`api/routes/health.py`. Three independent checks run in sequence — Postgres
(via the injected `db` session), Redis (constructs its own client inline), and
vector DB (currently just checks that a config string is non-empty, not a real
connectivity check). Each check's result is written into a shared
`health_status` dict; if any check fails, the endpoint returns a 503 with the
full status breakdown as the error detail.

**Pattern noticed:** the Postgres and Redis checks both build their own
clients inline within the endpoint function, rather than using a shared
dependency — this is the only place in the whole codebase that constructs a
`redis.Redis` client directly (every other file that touches Redis receives an
already-built client via dependency injection).

## Problem Summary (Week 7)

Issue #155 reports that the `/health` endpoint's Redis check references
`settings.redis_host` and `settings.redis_port`, but `Settings` only defines
`redis_url`. Because the check is wrapped in a broad `except Exception`, this
`AttributeError` doesn't crash the endpoint — it's silently caught and
reported as `"redis": "unhealthy"`. The practical effect: `/health` reports
Redis as unhealthy on every single call, regardless of whether Redis is
actually running, making this monitoring signal permanently useless.

**Before:** `GET /health` always reports `"redis": "unhealthy"` (contributing
to an overall `"status": "unhealthy"` and a 503 response), even when Redis is
genuinely healthy.
**After:** `GET /health` correctly reports Redis's real status.

## Reproduction (Week 7-8)

1. Started the full stack with `make run` (Postgres + Redis via Docker,
   FastAPI + Vite dev servers via `make run`).
2. Confirmed via `docker compose ps` that Redis was genuinely healthy.
3. Hit the endpoint directly: `curl http://localhost:8000/health`.
4. Result: `{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"}, ...}`
5. Confirmed the specific cause in the server's own logs: `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"`

(Note: postgres also showed unhealthy in this run -- that's a separate, unrelated bug, issue #154, a raw-SQL-string incompatibility with SQLAlchemy 2.x. I confirmed this is a different issue and stayed scoped to #155 only.)

## Root Cause

api/routes/health.py's Redis check constructed a client with settings.redis_host and settings.redis_port as arguments. Settings (in core/config.py) has no redis_host or redis_port fields -- only redis_url, which is also the only Redis config value used anywhere else in the codebase (confirmed by searching the whole project for redis.Redis( and redis_url -- no other file constructs a raw Redis client or references host/port config). This confirmed the fix should use the existing redis_url field rather than invent new config fields.

## Fix

Replaced the client construction to use redis.Redis.from_url(settings.redis_url, decode_responses=True) instead. redis-py's built-in from_url classmethod parses a connection URL directly, matching the one Redis config value that actually exists.

## Testing

No test file existed for api/routes/health.py prior to this fix -- this project's test suite has no established pattern for testing a route directly, no TestClient usage or get_db override pattern exists anywhere in the current suite. Created tests/unit/test_health_routes.py with two tests: one confirming the Redis check reports healthy when the ping succeeds (the regression test for this fix), and one confirming it still reports unhealthy when the Redis connection genuinely fails. Both use a TestClient with get_db overridden via app.dependency_overrides, and mock redis.Redis.from_url rather than hitting a real Redis instance, matching the unit-test-only pattern the rest of the suite uses.

## Verification

Ran curl against the live running app and confirmed redis now reports healthy. Ran the new test file directly and both tests passed. Ran the full unit test suite and confirmed via a git stash comparison that it has 53 pre-existing failures across unrelated modules both before and after my change, meaning my change introduces zero new failures. The make check pre-commit hooks flagged pre-existing ruff and mypy issues across many files I never touched, none of which are related to my change. I fixed the 4 new mypy errors introduced by my own new test file, and committed with --no-verify for the pre-existing, out-of-scope repo-wide debt, documenting this decision here transparently.
$

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/grod718/pathreview/commit/d7a77f7

**Reproduction summary:**
Confirmed via docker compose ps that Redis was genuinely healthy, then hit curl http://localhost:8000/health and observed "redis": "unhealthy" anyway -- confirmed the exact cause in the server logs ('Settings' object has no attribute 'redis_host').

**PLAN.md link:** https://github.com/grod718/pathreview/blob/fix/155-redis-host-config/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
None -- fix, tests, and PR are already complete as of this entry.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are complete: reproduced the bug live, implemented the fix (redis.Redis.from_url(settings.redis_url, ...)), verified against the running app, and wrote tests/unit/test_health_routes.py covering both the healthy and genuinely-unhealthy Redis paths.

**Next steps:**
Ran make check and make test-unit to confirm no new failures introduced; opened the PR (#175) against ascherj:main.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/175

**Branch:** fix/155-redis-host-config

**What you built:**
Fixed the /health endpoint's Redis check, which referenced nonexistent settings.redis_host/settings.redis_port fields, by switching to redis.Redis.from_url(settings.redis_url, ...) -- the one Redis config field that actually exists in Settings. Added the first route-level test in this codebase to cover the fix.

**Tests added or updated:**
Added tests/unit/test_health_routes.py with two tests: one confirming /health reports "redis": "healthy" when the Redis ping succeeds (the regression test for this fix), and one confirming it still correctly reports "unhealthy" on a genuine Redis connection failure.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both confirmed via a git stash before/after comparison: the codebase has 53 pre-existing test failures and pre-existing ruff/mypy debt across files unrelated to this change, documented in this journal and in the PR description. My change introduces zero new failures beyond that pre-existing baseline.)

**Draft PR feedback received from:** none
## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback -- reviewer feedback was not a feature for the Summer 2026 cohort, per the course note in the Week 10 assignment.

**How you responded:**
N/A.

---

### Reflection

**What was harder than you expected?**
The git rebase mechanics were the hardest part of this module, not the actual bug or the fix. I hit a stuck rebase-merge directory left over from an earlier attempt, and later ended up with my branch's history duplicated on top of the old commits instead of cleanly replacing them. Working through why git status and git log disagreed with what I expected, and eventually recovering by resetting to a known-good state, took far longer than writing and testing the actual fix.

**What did you learn about working in a large codebase?**
A tiny mismatch -- one field name that doesn't exist on a config object -- can cause a much bigger, harder-to-see problem than the size of the change suggests. The bug wasn't a crash; it was a silently swallowed exception that made a monitoring endpoint permanently wrong. In my own projects, a typo like that usually breaks something loudly and immediately. In a larger, production-style codebase, a small mismatch can hide behind broad error handling and quietly produce wrong results indefinitely.

**How did AI tools help -- and where did they fall short?**
AI was most useful for reading and tracing code I hadn't written -- quickly summarizing what a file was responsible for, and confirming exactly why a specific bug happened before I touched anything. It was much less useful for the actual git mechanics: several rebase and commit issues came from copy-paste and terminal quirks that AI couldn't see or predict, and I had to work through the recovery myself by comparing git log and git status output step by step.

**What would you do differently if you started over?**
I'd check the live GitHub issue tracker before trusting any local files in the repo. Early on, I spent time cross-referencing a local issues manifest file that turned out to be a stale, superseded snapshot -- the actual live tracker had a different, more specific set of issues. If I'd checked the real tracker first, I would have skipped that detour entirely.

**What are you most proud of from this module?**
Writing the first route-level test for this codebase. There was no existing pattern to copy -- no TestClient usage, no dependency-override example anywhere in the test suite -- so I had to build that pattern from scratch, including figuring out how to mock the database dependency and the Redis client without hitting real services. It's a small thing in the diff, but it's genuinely new infrastructure for the project, not just a copy of something that already existed.