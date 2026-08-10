
## Solution plan

**Issue:** #155 — Health check references `settings.redis_host`, which does not exist on `Settings`
**Reproduction commit link:** https://github.com/PlacidoG/pathreview/commit/d942fa6

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

- **Root cause:** `api/routes/health.py:45-46` builds the Redis client with
  `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`, but
  `core/config.py` `Settings` defines only `redis_url` — there is no `redis_host` or
  `redis_port` field. Reading the missing attribute raises `AttributeError`.
- **Why it's hidden:** the broad `except Exception` at `health.py:53` swallows the
  `AttributeError` and marks Redis `"unhealthy"` instead of surfacing a config error.
- **Expected:** when Redis is reachable, `/health` reports `redis: "healthy"`.
- **Actual:** `/health` reports `redis: "unhealthy"` and returns 503 even though Redis
  answers `PONG` — a false negative. The error fires *before* `ping()` is ever called.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- **Will edit (the fix):** `api/routes/health.py` — the Redis probe inside
  `health_check()` (lines 44-49). This is the only source file that needs changing.
- **Already exists, no edit needed (regression guard):** `tests/unit/test_health_check.py`
  — currently red; flips green when the fix lands.
- **Read-only reference (do NOT change):** `core/config.py` — the `Settings` class
  already exposes `redis_url`, which is the field the fix should use.
- **Not involved in the fix:** `scripts/seed_db.py` was only used to set up the DB for
  reproduction; it has nothing to do with the Redis config bug.

### Plan
What are the steps to fix this issue?

1. In `api/routes/health.py`, replace the `redis.Redis(host=settings.redis_host,
   port=settings.redis_port, ...)` call with
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)`, reusing the field
   that already exists. Keep the `ping()` call and the existing try/except structure.
2. (Optional, recommended) Narrow the `except Exception` to log the real error, or at
   least ensure the failure message is preserved, so a future config typo surfaces
   clearly instead of being masked.
3. Run `pytest tests/unit/test_health_check.py -v` and confirm it now **passes** (green).
4. Run the full unit suite (`make test-unit`) to confirm no regressions.
5. Verify end-to-end: `uvicorn api.main:app --port 8000`, then
   `curl -i http://127.0.0.1:8000/health` — the `redis` dependency should read
   `"healthy"`.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** the existing `settings.redis_url` value (e.g. `redis://localhost:6379/0`),
  loaded from `.env`/environment by `Settings`.
- **Output/behavior change:** the Redis probe successfully constructs a client and calls
  `ping()`. When Redis is up, `/health` reports `redis: "healthy"`; when Redis is truly
  down, it still correctly reports `"unhealthy"` (now for the real reason, not a config
  typo). No change to the response schema.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- **`/health` may still return 503 after this fix** — there is a *separate* bug in the
  Postgres probe (`await db.execute("SELECT 1")` needs `text("SELECT 1")` at
  `health.py:31`). Until that is also fixed, the overall status stays `unhealthy` even
  though Redis now reports healthy. The unit test passes because it mocks the DB; a live
  `curl` will not return 200 until the Postgres bug is handled too (likely a separate issue).
- **Regression risk is low** — the change is confined to the Redis block; it does not
  touch the Postgres or vector-DB probes.
- **`redis` package must be installed** in the runtime env (it is, via project deps).

### Edge cases
What inputs or states should your fix handle gracefully?

- **Redis genuinely down / wrong URL:** probe should report `"unhealthy"` via the
  `ping()` failure (a real connection error), not a config `AttributeError`.
- **`redis_url` with auth or a non-zero DB index** (e.g. `redis://:pass@host:6379/1`):
  `from_url` parses all of these, unlike the hard-coded `db=0` in the old code.
- **Slow/hanging Redis:** consider a socket connect/timeout so the health check can't
  hang indefinitely (optional hardening, not required for the fix).
