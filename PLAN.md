## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings — https://github.com/ascherj/pathreview/issues/155

### Understand

The `/health` endpoint reports whether PostgreSQL, Redis, and the vector DB are
reachable: it returns HTTP 200 when all are healthy and HTTP 503 if any is down.

Its Redis probe in [api/routes/health.py](api/routes/health.py#L44-L49) builds the
client with:

```python
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True,
)
```

But the `Settings` class in [core/config.py](core/config.py#L12) defines Redis
connection as a **single `redis_url` field** — there is no `redis_host` or
`redis_port`. So evaluating `settings.redis_host` raises
`AttributeError: 'Settings' object has no attribute 'redis_host'` *before* the
client is even constructed. The surrounding `try/except` in the route swallows
that error, records Redis as `"unhealthy"`, and sets the overall status to
`"unhealthy"`.

- **Expected:** With Redis running, `/health` reports `redis: "healthy"` and the
  endpoint returns 200.
- **Actual:** `/health` always reports `redis: "unhealthy"` and returns 503, even
  when Redis is up, because the probe crashes on a nonexistent config attribute.

Root cause: the health route reads config fields (`redis_host`, `redis_port`)
that do not exist; the real field is `redis_url`.

### Map

Files/functions involved:

- [api/routes/health.py](api/routes/health.py) — `health_check()`, the Redis
  probe block (lines ~39–56). **This is the only file that needs a code change.**
- [core/config.py](core/config.py) — `Settings`, which defines `redis_url`
  (line 12). Read-only reference; confirms the field to use. No change required.
- [tests/unit/test_health_route.py](tests/unit/test_health_route.py) — new
  reproduction test (added Week 8); the `xfail` marker gets removed once fixed.

Files I expect to touch when implementing the fix (Week 9):

1. `api/routes/health.py` — change the Redis client construction.
2. `tests/unit/test_health_route.py` — remove the `xfail` marker so it becomes a
   passing regression test; possibly add an "unhealthy when ping fails" case.

### Plan

1. **Rewrite the Redis probe to use the config that exists.** Replace the
   `redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)` call
   with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. This
   reuses the existing `redis_url` field instead of inventing new settings.
2. **Keep the failure path intact.** Leave the `try/except` so a genuinely
   unreachable Redis still records `"unhealthy"` and yields 503 — only the
   attribute crash goes away.
3. **Flip the reproduction test into a regression test.** Remove the
   `@pytest.mark.xfail` marker from `test_health_route.py`; it should now pass.
4. **Add a negative-path test.** Add a case where `ping()` raises, asserting
   Redis reports `"unhealthy"` and the endpoint returns 503, so the fix can't
   silently mask a real outage.
5. **Verify end to end.** With Docker services up, hit `GET /health` and confirm
   it returns 200 with `redis: "healthy"`; run `make test-unit`.

### Inputs & outputs

- **Input:** The health route reads `settings.redis_url` (default
  `redis://localhost:6379/0`) and the live reachability of the Redis server (via
  `ping()`).
- **Output / change:** The Redis probe returns `"healthy"` when Redis responds to
  `ping()` and `"unhealthy"` when it does not. Downstream, `GET /health` returns
  **200** when all dependencies are up (previously always 503 due to this bug).
  The JSON response schema is unchanged.

### Risks & unknowns

- **`from_url` argument compatibility.** Need to confirm `redis.Redis.from_url`
  accepts `decode_responses=True` alongside the URL (it does in redis-py ≥ 4/5,
  which this project pins via `redis>=5.0.0`). Low risk; verify against the
  installed version.
- **URL vs host/port semantics.** `redis_url` already encodes db index
  (`/0`), so passing `db=0` separately is unnecessary and could conflict. I'll
  drop the explicit `db=0` and let the URL carry it.
- **Other readers of the missing fields.** Need to grep the codebase for any
  other reference to `redis_host` / `redis_port` (e.g. caching or rate-limiting
  code) so I don't leave a second landmine. Initial search shows the only
  reference is in `health.py`, but I'll re-verify before the PR.
- **Sync client in an async route.** `redis.Redis(...).ping()` is a blocking
  call inside an async handler. Fixing that (async client) is out of scope for
  this issue; I'll keep the sync client to stay within the bug's blast radius and
  note it as a possible follow-up.

### Edge cases

- **Redis actually down:** `ping()` raises `redis.ConnectionError` → probe must
  record `"unhealthy"` and the endpoint must still return 503.
- **Malformed / empty `redis_url`:** `from_url` may raise on a bad URL → caught by
  the existing `try/except`, reported as `"unhealthy"` rather than crashing the
  request.
- **Redis up but slow / timing out:** should surface as `"unhealthy"` via the
  raised timeout, not hang the endpoint indefinitely (consider a short
  socket/connect timeout if not already implied by defaults).
- **All dependencies healthy:** endpoint returns 200 with every dependency
  marked `"healthy"` — the case the reproduction test pins.
