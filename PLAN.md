## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings — [#155](https://github.com/ascherj/pathreview/issues/155)

### Understand
The `/health` endpoint's Redis probe builds a `redis.Redis` client from
`settings.redis_host` and `settings.redis_port`. The `Settings` model
(`core/config.py`) never defines either field — the only Redis-related
setting it has is `redis_url` (e.g. `redis://localhost:6379/0`). Reading
`settings.redis_host` raises `AttributeError`. That error is caught by the
endpoint's own `except Exception` block, so the request doesn't crash, but
the Redis dependency is unconditionally marked `"unhealthy"` and the whole
health check returns `503` — even when Redis is running and reachable
(confirmed locally: `docker compose ps` shows the `redis` container healthy,
yet `GET /health` still reports `"redis": "unhealthy"`).

Expected behavior: when Redis is reachable, `/health` should report
`"redis": "healthy"` and return `200`. Actual behavior: `/health` always
reports `"redis": "unhealthy"` regardless of Redis's real state, because the
probe can never construct a working client.

### Map
- `api/routes/health.py` (lines 39-56) — the Redis probe block that
  constructs `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`
  and needs to be changed to use a connection value that actually exists.
- `core/config.py` (line 12) — defines `redis_url`, the only Redis setting
  currently on `Settings`. This is the value the fix should read from.
- `tests/integration/test_health.py` — new reproduction test asserting
  `/health` reports Redis as healthy; currently fails and should pass after
  the fix.
- `tests/unit/test_health_check.py` — new reproduction test asserting
  `Settings().redis_host` raises `AttributeError`; documents the root cause
  and should be removed or inverted once the fix lands.

### Plan
1. Update the Redis probe in `api/routes/health.py` to build the client from
   `settings.redis_url` via `redis.Redis.from_url(settings.redis_url, decode_responses=True)`
   instead of the nonexistent `redis_host`/`redis_port` fields.
2. Remove/replace `tests/unit/test_health_check.py`'s `AttributeError`
   assertion once the fix is in, or repurpose it into a regression test that
   `Settings` doesn't need `redis_host`/`redis_port` for the health check to
   work.
3. Update `tests/integration/test_health.py` to assert `/health` returns
   `200` with `"redis": "healthy"` when Redis is reachable (this test already
   exists as the reproduction and should flip to passing).
4. Add a negative-path test: point `redis_url` at an unreachable host/port
   (e.g. via monkeypatching `settings.redis_url`) and confirm `/health` still
   correctly reports `"redis": "unhealthy"` — so the fix doesn't just always
   report healthy regardless of real connectivity.
5. Run `make test-unit` and `make test-integration` locally to confirm both
   the existing suite and the new/updated health tests pass.

### Inputs & outputs
**Input:** `settings.redis_url` (a full Redis connection URL string, e.g.
`redis://localhost:6379/0`), already loaded from the `REDIS_URL` env var /
`.env` file by the existing `Settings` model — no new input needs to be
introduced.

**Output:** The `dependencies.redis` field in the `/health` JSON response
changes from being hard-coded to `"unhealthy"` on every request to correctly
reflecting real Redis connectivity (`"healthy"` when reachable,
`"unhealthy"` when not), which in turn changes whether the endpoint's overall
`status` triggers the `503` branch.

### Risks & unknowns
- `redis.Redis.from_url()` parses the URL differently than manually passing
  `host=`/`port=` (e.g. it also reads the DB index from the URL path) — need
  to confirm the parsed client behaves the same way `r.ping()` expects,
  by testing against the `redis` container in `docker-compose.yml`.
- Unclear whether other parts of the codebase (`agent/memory/session_store.py`,
  `safety/rate_limiter.py`, `safety/monitoring.py`, `agent/tools/market_analyzer.py`)
  that accept an injected `redis_client` expect it to be constructed the same
  way — worth checking whichever factory wires those up (not found yet) so
  the health check's construction pattern doesn't diverge from the rest of
  the app.
- The Postgres branch of the same health check independently fails today
  (`Textual SQL expression 'SELECT 1' should be explicitly declared as
  text('SELECT 1')` — a SQLAlchemy 2.0 issue, unrelated to #155). Need to be
  careful not to let that separate, pre-existing failure make it look like
  the Redis fix didn't work when testing manually against `/health`.

### Edge cases
- Redis reachable and responsive → `/health` reports `"redis": "healthy"`.
- Redis unreachable (wrong host/port, container down) → `/health` reports
  `"redis": "unhealthy"`, not a crash.
- `redis_url` malformed (e.g. missing scheme) → `redis.Redis.from_url()`
  should raise a clear error that's still caught by the existing
  `except Exception`, not an unhandled exception that bypasses the
  `"unhealthy"` status reporting.
- `REDIS_URL` env var unset → `Settings` falls back to its default
  (`redis://localhost:6379/0`), and the health check should behave the same
  as with an explicit value.
