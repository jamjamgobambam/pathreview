## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references settings.redis_host, which does not exist on Settings

**Tier:** [ X ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint (`api/routes/health.py`) checks Redis by building a client
with `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`. But the
`Settings` class in `core/config.py` never defines `redis_host` or `redis_port` — it
exposes a single `redis_url` instead. So the attribute lookup raises
`AttributeError: 'Settings' object has no attribute 'redis_host'` before a connection
is ever attempted. The surrounding `try/except` swallows that error, marks Redis
`"unhealthy"`, and the endpoint returns 503 regardless of whether Redis is actually
up — which defeats the point of a health check. A successful fix rebuilds the client
from the attribute that actually exists (`redis.Redis.from_url(settings.redis_url,
...)`), so `/health` reports Redis's real state instead of failing on a bad config
reference.

**Branch name:** fix/155-health-check-redis-host

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

---

### Selection notes — "Is this right for me?" checklist reasoning

- **Scope is bounded and understood.** The bug lives in one function in one file
  (`api/routes/health.py`). I traced it end to end with the VS Code debugger: sent a
  `GET /health`, hit a breakpoint in the Redis block, and read the caught exception
  in Locals — `AttributeError("'Settings' object has no attribute 'redis_host'")`.
  I can explain both the cause (attribute doesn't exist) and the effect (`except`
  swallows it, so the endpoint always returns 503).
- **The fix is small and low-risk.** Replace the `host=/port=` construction with
  `redis.Redis.from_url(settings.redis_url, ...)`, matching the attribute the
  `Settings` class already exposes. No schema, migration, or API-contract change.
- **I can verify it.** I have the backend running locally and a saved request that
  reproduces the 503, so I can confirm the Redis dependency flips to `"healthy"`
  (with Redis up) once the fix lands.
- **Out of scope, deliberately.** While reproducing this I noticed `/health` also
  reports Postgres unhealthy — but for a different reason (`db.execute("SELECT 1")`
  needs SQLAlchemy's `text()` wrapper). That is not issue #155. I'm leaving it
  untouched to keep this branch to one intent; it belongs in its own issue/PR.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [`5b12f9f`](https://github.com/tmayush/pathreview/commit/5b12f9f) — the added `tests/unit/test_health.py` encodes the reproduction: `test_health_check_does_not_reference_redis_host` asserts `settings` has no `redis_host`/`redis_port`, and before the fix the Redis block reported `"unhealthy"` because the attribute lookup raised `AttributeError`.

**Reproduction summary:**
I ran the backend and sent `GET /health` with a VS Code breakpoint in the Redis block. The caught exception was `AttributeError("'Settings' object has no attribute 'redis_host'")` — raised before any connection was attempted, then swallowed by the `except`, so the endpoint returned 503 with Redis marked `"unhealthy"` even though Redis was up.

**PLAN.md link:** [PLAN.md](https://github.com/tmayush/pathreview/blob/fix/155-health-check-redis-host/PLAN.md)

**Walkthrough video (recommended):** not recorded.

**Blockers or open questions:**
None. The fix is a bounded, one-function change; the only care needed is separating it from the codebase's documented pre-existing test/lint failures.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `api/routes/health.py` (sub-task 1) — the Redis client is now built with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. Added `tests/unit/test_health.py` (sub-task 2) with three passing tests.

**Next steps:**
Run the full `make check` / `make test-unit` baseline comparison (sub-task 3), finalize the journal, and open the PR (sub-task 4).

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/670

**Branch:** `fix/155-health-check-redis-host`

**What you built:**
The `/health` endpoint built its Redis client from `settings.redis_host`/`settings.redis_port`, attributes that don't exist on `Settings` — the lookup raised `AttributeError`, which was swallowed so Redis was always reported unhealthy and `/health` returned 503 even when Redis was up. The fix builds the client from the `settings.redis_url` that actually exists (via `redis.Redis.from_url`), so the check reports Redis's real state.

**Tests added or updated:**
Added `tests/unit/test_health.py` — the project's first health-endpoint tests: Redis reported healthy on a successful ping; reported unhealthy (503) on a real connection failure; and a regression guard confirming the client is built from `redis_url` and that `redis_host`/`redis_port` are never referenced.

**Self-review confirmation:** [ X ] make check passes  [ X ] make test-unit passes

_Pre-existing failures note:_ On the base commit (`main`), `make test-unit` reports **53 failing tests** (e.g. `test_tech_detector`, `test_skill_extractor`, `test_structural_chunker`) and `make check` reports pre-existing lint/type errors — all unrelated to issue #155. After my changes the count is unchanged (**53 pre-existing failures, +3 new passing tests**); my change introduces no new failures. My new test file passes lint cleanly, and the 4 lint hits in `health.py` are pre-existing in-function imports present identically on `main`. "Passes" here means my changes introduce no new failures.

**Draft PR feedback received from:** none