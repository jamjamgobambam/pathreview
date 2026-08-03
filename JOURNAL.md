## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint's Redis check tries to connect using `settings.redis_host`
and `settings.redis_port`, but the `Settings` model only defines a single combined
`redis_url` field. This caused an `AttributeError` every time the Redis check ran,
so the health endpoint always reported Redis as "unhealthy" even when Redis was
working fine. I fixed it by using `redis.Redis.from_url(settings.redis_url)` instead,
which correctly parses the existing connection string. This affects the `api/routes/health.py`
file and required no changes to the `core/config.py` settings themselves.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/unt-akanksha/pathreview/commit/adf2337

**Reproduction summary:**
I called `GET /health` locally and confirmed it returned a 503 with
`"redis": "unhealthy"`, even though the Redis Docker container was running
and healthy. Checking the code showed `settings.redis_host`/`settings.redis_port`
don't exist on the `Settings` model, causing an `AttributeError` that was
silently caught and reported as an unhealthy status.

**PLAN.md link:** https://github.com/unt-akanksha/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** [not recorded — optional/ungraded]

**Blockers or open questions:**
None currently. One thing I noted in PLAN.md: fixing this surfaced an
unrelated pre-existing bug (issue #154, raw SQL string not wrapped in
`text()`), which I intentionally left out of scope for this fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Fix, tests, PLAN.md, and reproduction were already completed in Weeks 7-8. This week's focus was running the full make check/make test-unit suite to document pre-existing failures, then opening the PR.

**Next steps:**
Open the PR and fill in the full template, including documenting pre-existing failures unrelated to my change.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/628

**Branch:** fix/155-health-check-redis-host

**What you built:**
Fixed the `/health` endpoint's Redis check, which referenced nonexistent `settings.redis_host`/`settings.redis_port` fields, causing an `AttributeError` that made the health check always report Redis as unhealthy regardless of its real status. Replaced it with `redis.Redis.from_url(settings.redis_url)`, using the connection field that actually exists on the `Settings` model.

**Tests added or updated:**
Added `tests/unit/test_health.py` with two tests: one confirming Redis reports "healthy" on a successful mocked connection, one confirming a genuine connection failure is still correctly reported as "unhealthy."

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both pass for my changed files specifically; the full suite has 178 pre-existing lint errors and 53 pre-existing test failures in unrelated modules, documented in the PR description — my changes introduce no new failures.)

**Draft PR feedback received from:** none