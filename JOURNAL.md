## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/155](https://github.com/ascherj/pathreview/issues/155)

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The Redis probe in `api/routes/health.py` reads `settings.redis_host`, but the `Settings` model in `core/config.py` does not define that field. As a result, a request to `GET /health` raises an `AttributeError` before the endpoint can report Redis health. A successful fix will make the health endpoint use configuration that actually exists and allow it to return Redis status without crashing.

**Branch name:** `fix/155-health-check-redis-config`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [7a9af707c5535d25e0589832245d37477377fe9c](https://github.com/ascherj/pathreview/commit/7a9af707c5535d25e0589832245d37477377fe9c)

**Reproduction summary:**
I started the backing services and requested `GET /health`. The Redis probe failed because
`health.py` references `settings.redis_host` and `settings.redis_port`, while the `Settings`
model defines only `redis_url`.

**PLAN.md link:** [PLAN.md](https://github.com/pk1098/pathreview/blob/fix/155-health-check-redis-config/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Added the missing `redis_host` and `redis_port` settings required by the Redis health check and
documented the reproduction and solution plan. Added a focused unit test for the Redis probe and
the health-route type annotations required by mypy.

**Next steps:**
Run the focused test and final quality checks, push the test commit, and respond to PR feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** [ascherj/pathreview#840](https://github.com/ascherj/pathreview/pull/840)

**Branch:** `fix/155-health-check-redis-config`

**What you built:**
Added `redis_host` and `redis_port` to the application settings so the `/health` endpoint can
construct a Redis client and accurately report Redis availability. Added explicit health-route
types so the new test and route pass static analysis.

**Tests added or updated:**
Added `tests/unit/test_health.py`. It mocks Redis, verifies that the health check constructs the
client with `settings.redis_host` and `settings.redis_port`, confirms `PING` is called, and checks
that Redis and the overall response are reported as healthy.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none
