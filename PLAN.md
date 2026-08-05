## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings —
https://github.com/ascherj/pathreview/issues/155

### Understand

The `/health` endpoint reports the status of PostgreSQL, Redis, and the vector DB. Its Redis
probe constructs a client with `redis.Redis(host=settings.redis_host, port=settings.redis_port,
...)`. Neither `redis_host` nor `redis_port` is defined on the `Settings` model in
`core/config.py` — the only Redis-related field is `redis_url`.

- **Expected:** `GET /health` runs the Redis probe, pings Redis, and reports
  `redis: "healthy"` (or `"unhealthy"` if the ping fails).
- **Actual:** As soon as execution reaches the Redis block, Python raises
  `AttributeError: 'Settings' object has no attribute 'redis_host'`, so the Redis status is
  never determined and the request errors out.

Root cause: the health check reads config fields that were never added to `Settings`. The
existing, correct field is `settings.redis_url`.

### Map

Files involved:

- `api/routes/health.py` — the endpoint; the Redis probe (the buggy lines) lives here.
- `core/config.py` — the `Settings` model; confirms `redis_url` exists and `redis_host`/
  `redis_port` do not.
- `tests/unit/test_health_route.py` — new test file for the endpoint (no `/health` tests
  exist today).

Files I expect to touch: `api/routes/health.py` (the fix) and `tests/unit/test_health_route.py`
(new tests). `core/config.py` is read-only reference — no change needed, because I am reusing
the existing `redis_url` rather than adding new host/port fields.

### Plan

1. **Reproduce** the AttributeError locally: `python -c "from core.config import settings;
   settings.redis_host"` and by hitting `GET /health`, confirming the Redis block is where it
   fails.
2. **Fix the probe** in `api/routes/health.py`: replace
   `redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)`
   with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`, which parses host,
   port, and db index straight from `redis_url`.
3. **Add tests** in `tests/unit/test_health_route.py`: (a) reachable Redis → `/health` returns
   200 with `redis: "healthy"` and the client is built from `redis_url`; (b) failing `ping()` →
   `redis: "unhealthy"` and HTTP 503; (c) a guard asserting `Settings` has no `redis_host`/
   `redis_port` and does have `redis_url`.
4. **Verify** with `pytest tests/unit/test_health_route.py -m unit`, plus `ruff`/`black` on the
   changed files, and confirm no new lint/type errors are introduced.

### Inputs & outputs

- **Input:** `settings.redis_url` (e.g. `redis://localhost:6379/0`).
- **Output / change:** the Redis probe no longer raises `AttributeError`; `GET /health` returns
  a JSON body whose `dependencies.redis` is `"healthy"` when the ping succeeds and `"unhealthy"`
  (with overall status `"unhealthy"` → HTTP 503) when it fails. No config schema change; no
  change to any other dependency check.

### Risks & unknowns

- **Other unrelated failure in the same endpoint:** `api/routes/health.py` also runs
  `db.execute("SELECT 1")`, which fails under SQLAlchemy 2.x with "Textual SQL expression ...
  should be explicitly declared as text('SELECT 1')". This is a *separate* bug (out of scope for
  #155) but it makes `GET /health` return 503 overall, so I must assert on the `redis`
  sub-status specifically, not the top-level status, when verifying my fix.
- **`from_url` semantics:** need to confirm `redis.Redis.from_url` honors a `/0` db index and
  any auth in the URL the same way the old host/port client did — verified against the `redis`
  package (`redis>=5.0`, `types-redis` in dev deps).
- **Tests hitting real services:** the unit tests must not require a live Redis/DB, so I mock
  `redis.Redis.from_url` and override the `get_db` FastAPI dependency; risk is getting the async
  dependency override right.

### Edge cases

- **Redis down / unreachable:** `ping()` raises `ConnectionError` → probe must catch it and
  report `redis: "unhealthy"` (→ 503), not crash.
- **Malformed or empty `redis_url`:** `from_url` may raise on a bad URL → handled by the existing
  `try/except` around the Redis block, reported as `unhealthy`.
- **`redis_url` with auth or non-default db** (e.g. `redis://:pass@host:6379/2`): `from_url`
  should parse these; the old host/port approach silently ignored them.
- **Redis healthy but Postgres/vector unhealthy:** overall status still degrades to unhealthy —
  the Redis fix must not mask other dependency failures.
