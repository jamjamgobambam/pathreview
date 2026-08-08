## Solution plan

**Issue:** #155 — Health check references `settings.redis_host`, which does not exist on Settings

### Understand

`api/routes/health.py` has a `redis` try/except block (lines 39–56) that builds a client with
`redis.Redis(host=settings.redis_host, port=settings.redis_port, ...)`. `Settings` in
`core/config.py` never defines `redis_host` or `redis_port` — the only Redis-related field is
`redis_url: str = Field(default="redis://localhost:6379/0")` (line 12). Accessing
`settings.redis_host` raises `AttributeError: 'Settings' object has no attribute 'redis_host'`.

**What I confirmed by actually reproducing it** (not just reading the code): I ran the app
locally (`docker compose up -d`, `alembic upgrade head`, `uvicorn api.main:app`) and hit
`GET /health`. The `AttributeError` really does fire, exactly as the issue says — but it does
**not** crash the endpoint the way the issue description implies. It's caught by the existing
`except Exception as exc:` block at line 53, logged, and turned into
`"redis": "unhealthy"` in the response body:

```
2026-07-29 00:45:07 [error] redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"
```

```json
{"detail":{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"},...}}
```
`HTTP 503`

So the real bug isn't an unhandled crash — it's a **false negative that can never be fixed by
Redis itself being healthy**. Even with Redis fully up (confirmed via `docker compose ps` →
`healthy`), `/health` will always report `redis: unhealthy`, because the code never gets far
enough to actually ping Redis. That's arguably worse for an on-call engineer than a loud crash:
the endpoint looks like it's doing a real check but the result is meaningless.

(Side note: I also observed `postgres: unhealthy` in the same response, caused by a different,
already-tracked bug — raw `"SELECT 1"` needs `text()` for SQLAlchemy 2.x. That's a separate
issue from #155 and I'm leaving it alone — see Risks below.)

**Root cause:** `api/routes/health.py`'s Redis probe reads config fields that were never added
to `Settings`.

**Fix direction:** Use `redis.Redis.from_url(settings.redis_url)` instead of constructing the
client from `host=`/`port=`. This uses the field that already exists, needs no changes to
`core/config.py`, and is the standard `redis-py` entry point for a connection string — so it's
a smaller diff than adding two new `Settings` fields that would just duplicate what `redis_url`
already encodes.

### Map

Files I expect to touch:
- `api/routes/health.py` (lines 39–56) — replace the `redis.Redis(host=..., port=...)` call
  with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
- `tests/unit/test_health.py` (new file) — first test coverage for this endpoint. Following the
  convention in `tests/unit/test_resume_parser.py`: `@pytest.mark.unit` on a test class,
  `unittest.mock.patch` for external dependencies (no existing `tests/api/` directory or
  `TestClient` usage anywhere in the repo yet, so this also establishes the pattern for future
  route tests).
- `core/config.py` — not touching. Confirmed `redis_url` already covers what's needed once the
  fix uses `from_url`.

### Plan

1. Confirm `redis.Redis.from_url()` accepts a full `redis://host:port/db` string and exposes
   `.ping()` the same way the current `host=`/`port=` constructor does (checked: it does — same
   class, just a different entry point).
2. Edit `api/routes/health.py`: replace lines 44–49 with
   `r = redis.Redis.from_url(settings.redis_url, decode_responses=True)`.
3. Manually re-run `GET /health` locally and confirm `redis` now reports `"healthy"` (Redis
   container is already up and healthy in `docker compose ps`).
4. Add `tests/unit/test_health.py`:
   - override the `get_db` dependency with a fake session whose `execute()` doesn't raise, so
     the Postgres branch doesn't interfere with the Redis-specific test
   - patch `redis.Redis.from_url` to return a mock whose `.ping()` succeeds → assert
     `dependencies.redis == "healthy"`
   - patch it to raise (e.g. `redis.exceptions.ConnectionError`) → assert
     `dependencies.redis == "unhealthy"` and no unhandled exception escapes the route
   - a regression test that directly asserts `settings.redis_host` is never referenced (i.e.
     the fixed code no longer touches a nonexistent attribute) — really just covered by the
     two cases above passing without `AttributeError`
5. Run `make test-unit` to confirm the new tests pass and nothing else broke.
6. Run `make check` (ruff + black + mypy) before opening the PR.

### Inputs & outputs

**Function I'm changing:** the Redis block inside `health_check()` in `api/routes/health.py`.

**Existing (broken) behavior:**
- Input: any request to `GET /health`, Redis reachable or not
- Output: `dependencies.redis` is always `"unhealthy"` (masked by the `AttributeError`)

**New behavior:**
- Input: `GET /health`, Redis reachable → Output: `dependencies.redis == "healthy"`
- Input: `GET /health`, Redis unreachable (e.g. connection refused) →
  Output: `dependencies.redis == "unhealthy"`, still a clean 503, no unhandled exception

**Tests I'll write** (`tests/unit/test_health.py`):

```python
@pytest.mark.unit
class TestHealthCheck:
    async def test_health_check_redis_healthy(self, ...):
        # patch redis.Redis.from_url(...).ping() to succeed
        # assert response body dependencies["redis"] == "healthy"

    async def test_health_check_redis_unreachable(self, ...):
        # patch redis.Redis.from_url(...).ping() to raise ConnectionError
        # assert dependencies["redis"] == "unhealthy", no 500, no AttributeError
```

I'll check how `get_db` is imported in `api/routes/health.py` to decide the cleanest way to
override it in tests (`app.dependency_overrides[get_db] = ...` vs. patching the import site).

### Risks & unknowns

1. **Postgres bug is out of scope, on purpose.** I confirmed `postgres: unhealthy` is caused by
   a different bug (`"SELECT 1"` not wrapped in `text()`), already the subject of other PRs
   (#177, #188, #208 — see issue #155 discussion). I'm intentionally not fixing it here to keep
   this PR scoped to #155; mentioning it explicitly so it isn't mistaken for something I missed.
2. **`from_url` vs. `host=`/`port=` argument differences.** `redis.Redis.from_url()` parses
   `db` from the URL path (`/0`) automatically; the old code passed `db=0` explicitly. Need to
   confirm the parsed URL's db index matches what the old hardcoded `db=0` assumed — it does for
   the default `redis://localhost:6379/0`, but I should not assume every possible `REDIS_URL`
   value in `.env.example`/prod configs is `/0`. I'll trust the URL rather than hardcoding.
3. **Mocking `redis.Redis.from_url` where it's imported locally.** `import redis` happens
   inside the function body in `health.py`, not at module level. `unittest.mock.patch` needs to
   target `"redis.Redis.from_url"` (patching the class method on the `redis` module itself)
   rather than `"api.routes.health.redis.Redis"`, since there's no module-level `redis` name to
   patch. I'll verify this works before assuming the mock takes effect.
4. **Whether the multiple already-open PRs (#160, #177, #188, #208) beat me to this.** Real risk
   noted in my Week 7 journal — if one of them merges first, I'll rebase my scoped, single-issue
   version on whatever lands, or pivot to a different open issue.

### Edge cases

- Redis reachable and healthy → `"healthy"`, overall `status` unaffected by this check.
- Redis process down / connection refused → `"unhealthy"`, 503, no unhandled exception (this is
  the case the current code silently gets "right" by accident, since it's masked either way —
  need my test to prove it's right for the *correct* reason now).
- Malformed `REDIS_URL` (e.g. missing scheme) → `redis.Redis.from_url()` raises `ValueError`
  before `.ping()` is ever called; this is still caught by the existing outer
  `except Exception as exc:`, so behavior degrades gracefully to `"unhealthy"` rather than a
  500. I'll add a short comment noting this is intentional, not accidental.
- Vector DB and other dependencies are untouched by this change — confirmed by the fact that
  `vector_db: "healthy"` already appears correctly in my reproduction output above.
