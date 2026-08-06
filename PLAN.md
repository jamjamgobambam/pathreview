# Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings (#155)](https://github.com/ascherj/pathreview/issues/155)

## Understand

The `/health` endpoint's Redis check builds a `redis.Redis(...)` client using
`settings.redis_host` and `settings.redis_port`. `Settings` (`core/config.py`)
only defines `redis_url`, so referencing those two fields raises an
`AttributeError` on every request. The broad `except Exception` around the
Redis check swallows it and reports `"redis": "unhealthy"`, so the endpoint's
*actual* behavior is "always report Redis down," while the *expected* behavior
is "report Redis's real status" — healthy when Redis is reachable, unhealthy
only on a genuine connection/ping failure. See `REPRODUCTION.md` for the
captured error and endpoint output confirming this.

## Map

Files/functions involved:

- `api/routes/health.py` — `health_check()`, specifically the Redis `try` block
  (lines ~40-53 in the pre-fix version) that constructs the `redis.Redis` client.
- `core/config.py` — `Settings` class, which defines `redis_url` (the field that
  actually exists and should be used instead).
- `tests/unit/test_health_check.py` — new test file to cover this endpoint,
  since no existing test exercised `/health` before this fix.

## Plan

1. Replace the `redis.Redis(host=..., port=...)` construction in
   `api/routes/health.py` with `redis.Redis.from_url(settings.redis_url, ...)`,
   which parses host/port/db directly from the URL already defined on `Settings`.
2. Add type annotations to `health_check()` (`db: Annotated[AsyncSession, Depends(get_db)]`,
   return type `dict[str, Any]`) so the fixed code passes the repo's `mypy`
   pre-commit hook — this surfaced a second, unrelated pre-existing bug
   (raw SQL string passed to `db.execute()`, tracked separately as issue #154),
   which I suppressed with a scoped `# type: ignore` comment rather than fixing,
   to keep this PR limited to #155.
3. Write `tests/unit/test_health_check.py` covering two cases: (a) Redis client
   is built from `settings.redis_url` and reports `"healthy"` when `ping()`
   succeeds, and (b) a real Redis outage (`ping()` raising `ConnectionError`)
   still correctly surfaces as `"unhealthy"` via the `503` response.
4. Run `ruff`, `black`, and `mypy` against the changed files only (not the
   whole repo, to avoid unrelated reformatting noise) and confirm the repo's
   `pre-commit` hooks pass cleanly on commit.
5. Verify manually against a running `make run` instance that `GET /health`
   returns `"redis": "healthy"` when Redis is up, matching the behavior
   `docs/SETUP.md` implies the endpoint should have.

## Inputs & outputs

- **Input:** `settings.redis_url` (a `str`, e.g. `redis://localhost:6379/0`,
  loaded from `.env`/environment by `Settings` in `core/config.py`).
- **Output:** the `health_status["dependencies"]["redis"]` field in the
  `health_check()` response — now correctly `"healthy"` or `"unhealthy"`
  based on `redis.Redis.from_url(...).ping()`'s actual outcome, instead of
  being hardcoded-in-practice to `"unhealthy"` by the `AttributeError`.
- No changes to the endpoint's external contract: same route (`GET /health`),
  same response shape, same `200`/`503` status code semantics.

## Risks & unknowns

- `redis.Redis.from_url()` accepts `decode_responses` as a kwarg the same way
  the old constructor did — confirmed by checking `redis-py`'s API before
  swapping it in, but worth re-checking if `redis-py` is ever upgraded past
  what's pinned (`redis>=5.0.0` in `pyproject.toml`).
- Adding type annotations to `health_check()` in `api/routes/health.py`
  surfaced the pre-existing `db.execute("SELECT 1")` mypy error (issue #154).
  Risk: if #154 is fixed independently before this PR merges, my `type: ignore`
  comment on that line will become dead and should be removed — flagged
  explicitly in code comments and in this plan so it isn't missed.
- No existing tests covered `api/routes/health.py` before this change, so
  there's some risk the new tests' mocking approach
  (`patch("redis.Redis.from_url", ...)`) diverges from how the team prefers
  to test FastAPI routes elsewhere in the codebase — checked `tests/unit/test_security.py`
  for existing conventions (`@pytest.mark.unit`, `unittest.mock.patch`) to
  stay consistent.

## Edge cases

- **Redis is reachable but slow/times out:** `ping()` should raise a
  `redis.exceptions.TimeoutError` (a subclass of the base `RedisError`), which
  is still caught by the existing `except Exception` and correctly reported
  as `"unhealthy"` — covered indirectly by the `ping().side_effect = ConnectionError(...)`
  test case.
- **`REDIS_URL` is malformed or empty in `.env`:** `redis.Redis.from_url()`
  raises a `ValueError` while parsing, before `ping()` is ever called — this
  is still caught by the same `except Exception` block, so the endpoint still
  degrades gracefully to `"unhealthy"` instead of crashing with an unhandled
  500, same as the genuine-outage case above.
