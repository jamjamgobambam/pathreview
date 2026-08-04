## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155
**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` tries to connect to Redis using `settings.redis_host` and `settings.redis_port`, but `core/config.py` only defines a single `redis_url` field — it never defines separate host/port fields. This causes an `AttributeError` every time the Redis check runs, which is caught by the endpoint's exception handling and silently reported as `"redis": "unhealthy"`, so the health check always fails on Redis even when Redis is running fine. A successful fix would update the Redis check to use the existing `redis_url` field (either by parsing it or connecting via `redis.from_url()`) so the health check accurately reflects Redis's real status.

**Scope reasoning ("Is this right for me?" checklist):**
I chose issue #155 because it's a well-scoped Tier 1 fix: the bug is isolated to a single function (`health_check` in `api/routes/health.py`), the root cause is already clear from reading the code (two undefined config fields), and the fix doesn't require touching other modules or understanding unfamiliar business logic. It's also easy to verify locally — I can call `GET /health` before and after the fix and see the Redis status change. Since this is my first time contributing to a large codebase, this level of contained, single-function scope felt like the right entry point rather than something involving multiple files or unclear requirements.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sandhya8109/pathreview/commit/53b4444a1a9e50870aa0875db85b7cc3f0955cf6

**Reproduction summary:**
Ran the app locally and called `GET http://localhost:8000/health`. The response returned a 503 with `"redis": "unhealthy"`, and the Uvicorn logs confirmed the exact root cause: `redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"` — matching the issue exactly. (Note: `postgres` also showed unhealthy in this run, but that's a separate, unrelated SQLAlchemy 2.x text() issue — not part of #155.)

**PLAN.md link:** 
https://github.com/sandhya8109/pathreview/blob/fix/155-health-check-redis-host/PLAN.md

**Walkthrough video (recommended):** [optional — skip or add later]

**Blockers or open questions:**
Need to confirm whether other files in the codebase also reference `settings.redis_host`/`settings.redis_port` besides `health.py`, and haven't yet located the test file for this route.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix for issue #155: replaced the broken `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)` call in `api/routes/health.py` with `redis.from_url(settings.redis_url, decode_responses=True)`, using the config field that actually exists. Verified locally in both directions — with Redis running, `/health` correctly reports `"redis": "healthy"`; with Redis stopped, it reports `"redis": "unhealthy"` for a genuine connection error rather than the old `AttributeError`. Also wrote a full test suite (`tests/unit/test_health.py`, 7 tests) covering the Redis healthy/unhealthy paths, a regression test confirming `redis_url` is used instead of the undefined fields, and the Postgres/vector_db checks and overall response shape. Cleaned up a pre-existing unused `timedelta` import and import ordering in `health.py` while I was in the file. This covers sub-tasks 1–4 of my `PLAN.md` (grep for other references, locate test file, implement the fix, verify both healthy/unhealthy cases) plus sub-task 5 (write tests).

**Next steps:**
Run `make check` and `make test-unit` against the full suite to confirm no new failures (done — confirmed 53 pre-existing failures unrelated to my change, `test_health.py` passes 7/7 clean). Open a draft PR on `pathreview` for early feedback, fill in the PR template, and get peer/mentor review before finalizing.

**Blockers:**
None currently. One open question I noted in `PLAN.md`: whether `redis.from_url()` handles every option the old `host`/`port` approach implicitly assumed (e.g. auth/TLS) — not an issue for this local setup, but worth a mentor's eyes on the PR in case it matters for other environments.