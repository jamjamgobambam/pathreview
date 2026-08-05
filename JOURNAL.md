# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check in `api/routes/health.py` tries to connect using
`settings.redis_host` and `settings.redis_port`, but the `Settings` config class only
defines a single `redis_url` field — those two attributes don't exist. As a result, the
Redis check always throws an `AttributeError`, and the whole health endpoint reports
"unhealthy" even when Redis is running fine. A correct fix connects using the existing
`redis_url` (e.g. via `redis.Redis.from_url()`) so the health check accurately reflects
Redis's real status. This also has zero existing test coverage, so part of the fix is
adding a test for the `/health` endpoint.

**Scope reasoning:** This is my first open-source contribution, so I chose a Tier 1 issue
per the checklist. It's isolated to one function in one file, the root cause is already
confirmed by reproducing the bug locally, and it's realistically a 1-2 hour fix plus test
writing — well within the Tier 1 time estimate. This issue already has significant activity
from other students (several claim comments and a few open PRs); per the contribution
checklist, claims are non-exclusive and my grade comes from my own artifacts, so I'm
proceeding, but will implement and write it up independently rather than referencing
anyone else's PR.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/BettinaGeorge/pathreview/commit/a9dcec0

**Reproduction summary:**
I wrote `tests/unit/test_health.py`, which calls `health_check()` directly with a mocked
database dependency. One test confirms the root cause directly — the real `Settings`
object has no `redis_host`/`redis_port` fields, only `redis_url`. The second test calls
the actual route function and confirms it raises `HTTPException(503)` with
`dependencies.redis == "unhealthy"` even though Postgres reports healthy — proving the
`AttributeError` from the missing settings field is silently caught by the route's broad
`except Exception` block rather than surfacing as a crash.

**PLAN.md link:** https://github.com/BettinaGeorge/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Before implementing the fix, I need to grep the codebase for any other `redis.Redis(...)`
call sites to confirm `api/routes/health.py` is the only place that needs to change.
Separately, running mypy against this file surfaced several pre-existing type errors in
`health.py` unrelated to this issue (missing type annotations, dict-indexing errors on a
loosely-typed `health_status` object) — I bypassed the pre-commit hook for my reproduction
commit since those errors predate my change, but I'll decide in Week 9 whether cleaning
them up belongs in this PR's scope, since I'll already be editing that exact function.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks 1-2 from `PLAN.md`: grepped the codebase for other `redis.Redis(...)`
call sites and confirmed `api/routes/health.py` is the only one, then replaced the broken
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)` construction with
`redis.Redis.from_url(settings.redis_url, decode_responses=True)`.

**Next steps:**
Update `tests/unit/test_health.py` (sub-task 4) so it verifies the fixed behavior instead
of just documenting the bug — flip the end-to-end test to expect `"healthy"`, and add a
new test confirming a genuinely unreachable Redis is still correctly reported as
`"unhealthy"`. Then run `make check` and `make test-unit` to confirm no new failures
(sub-task 5), and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/990

**Branch:** fix/155-health-check-redis-host

**What you built:**
Fixed the `/health` endpoint's Redis probe, which crashed with an `AttributeError` because
it referenced `settings.redis_host`/`settings.redis_port` — fields that don't exist on
`Settings` (only `redis_url` does). The endpoint now connects via
`redis.Redis.from_url(settings.redis_url)`, so it correctly reports Redis's real status
instead of always returning a 503.

**Tests added or updated:**
Updated `tests/unit/test_health.py` (3 tests total): one confirms the root cause directly
(`Settings` has no `redis_host`/`redis_port` fields, only `redis_url`), one confirms a
reachable Redis now reports `"healthy"` with a 200 response instead of the old 503, and one
covers the edge case that a genuinely unreachable Redis still correctly reports
`"unhealthy"` rather than the fix silently masking real outages.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: this codebase has documented pre-existing failures unrelated to this issue —
53 pre-existing test failures across 16 unrelated files, 100 pre-existing mypy errors
across 26 files including 8 in `health.py` itself, and 183 pre-existing ruff errors in
files I didn't touch. I confirmed all of these counts are identical before and after my
change, so "passes" here means my change introduces no new failures, per the
pre-existing-failures guidance for this week. Full breakdown is documented in the PR
description.)

**Draft PR feedback received from:** none — opened directly as ready for review due to
the submission deadline having passed; reaching out to the course team separately about
the late submission.
