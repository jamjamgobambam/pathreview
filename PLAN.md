## Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings — #155](https://github.com/ascherj/pathreview/issues/155)

### Understand

The `/health` endpoint (`api/routes/health.py`) builds its Redis client with
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`. The
`Settings` class in `core/config.py` never defines `redis_host` or `redis_port`
— it exposes a single `redis_url` field (default `redis://localhost:6379/0`).

- **Expected:** `/health` connects to Redis and reports its real state
  (`"healthy"` when reachable, `"unhealthy"` when the connection fails).
- **Actual:** `settings.redis_host` raises
  `AttributeError: 'Settings' object has no attribute 'redis_host'` *before any
  connection is attempted*. The surrounding `try/except` swallows the error,
  marks Redis `"unhealthy"`, and the endpoint returns **503 unconditionally** —
  even when Redis is up. The health check can never report Redis healthy.

**Root cause:** the endpoint references configuration attributes that don't
exist on `Settings`; it should build the client from the `redis_url` that does.

### Map

- `api/routes/health.py` — the Redis check block (the only production code
  change). Swap the `host=/port=` construction for `redis.Redis.from_url`.
- `core/config.py` — read-only reference; confirms `redis_url` is the real
  attribute and `redis_host`/`redis_port` do not exist. No change needed.
- `tests/unit/test_health.py` — **new** test file (no health tests exist today).
- `safety/rate_limiter.py`, `agent/memory/session_store.py` — reviewed to
  confirm the rest of the app already receives a Redis client by injection and
  does not depend on the removed attributes. No change needed.

### Plan

1. In `api/routes/health.py`, replace
   `redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)`
   with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`
   (the URL already encodes host, port, and db).
2. Add `tests/unit/test_health.py` covering: Redis reported healthy on a
   successful ping; reported unhealthy (503) on a real connection failure; and a
   regression guard asserting the client is built from `redis_url` and that
   `settings` has no `redis_host`/`redis_port`.
3. Run `make test-unit` and `make check`; record pre-existing failures vs. new
   ones (the codebase has documented pre-existing failures unrelated to #155).
4. Update `JOURNAL.md` (Week 8 + Week 9 check-ins) and open the PR.

### Inputs & outputs

- **Input:** `settings.redis_url` (str, from env/.env, default
  `redis://localhost:6379/0`).
- **Output:** a working Redis client; the `dependencies.redis` field in the
  `/health` JSON reflects Redis's true state, and the endpoint returns 200 when
  all dependencies are healthy instead of always 503.

### Risks & unknowns

- **`from_url` argument parity:** `db=0` is dropped because it's already encoded
  in the URL's path (`/0`). Low risk — the default URL uses db 0. Verified
  against `core/config.py`.
- **Pre-existing failures:** `make check` and `make test-unit` already report
  unrelated failures (e.g. `test_tech_detector`, `test_skill_extractor`) and
  lint errors on the base commit. Risk is misattributing them to this change —
  mitigated by capturing a baseline on `main` before/after.
- **Out of scope:** `/health`'s Postgres check (`db.execute("SELECT 1")` needs
  SQLAlchemy's `text()` wrapper) is a separate bug; deliberately not touched to
  keep this branch to one intent.

### Edge cases

- Redis is down / unreachable → `ping()` raises → reported `"unhealthy"`, 503
  (the intended behavior, now reachable instead of masked by the config bug).
- A non-default `redis_url` (different host/port/db via env) → honored, because
  the client is built from the URL rather than hard-coded pieces.
- `settings.redis_url` malformed → `from_url` raises inside the `try`, caught and
  reported `"unhealthy"` — a real signal, not a silent config crash.
