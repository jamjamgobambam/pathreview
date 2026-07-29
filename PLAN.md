## Solution plan

**Issue:** [#155 — Health check references `settings.redis_host`, which does not exist](https://github.com/ascherj/pathreview/issues/155)

### Understand

**Root cause:** `api/routes/health.py` builds its Redis client with:

```python
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True,
)
```

`core/config.py`'s `Settings` model has no `redis_host` or `redis_port` field. Redis is
configured as a single URL string instead:

```python
redis_url: str = Field(default="redis://localhost:6379/0")
```

**Expected behavior:** `/health` reports the true status of Postgres, Redis, and the vector DB,
returning 200 when all are reachable and 503 when one genuinely is not.

**Actual behavior:** Accessing `settings.redis_host` raises `AttributeError`. That exception is
caught by the broad `except Exception` at line 53, so it's misreported as "Redis unreachable"
rather than surfaced as a config bug. Because `health_status["status"]` is set to `"unhealthy"`
whenever any dependency fails, this makes the endpoint return HTTP 503 unconditionally — even
when Postgres, Redis, and the vector DB are all fully healthy. The `r.ping()` call is never
reached, so the probe never actually tests connectivity.

### Map

Files involved:

- `api/routes/health.py` — contains the bug (lines 44–49) and the route itself. **Will change.**
- `core/config.py` — defines `Settings`; confirms `redis_url` exists and `redis_host`/`redis_port`
  do not. **Read-only reference**, no change needed here.
- `tests/unit/test_health.py` — did not exist before this issue. **New file**, added to cover the
  endpoint's dependency probes.

No other module reads `settings.redis_host` or `settings.redis_port` (confirmed via repo-wide
search), so the blast radius is contained to this one route.

### Plan

1. **Reproduce first.** Write `tests/unit/test_health.py` against the *current* code and confirm
   it fails with the exact `AttributeError` the issue describes, so the bug is proven before
   anything is touched. (Done — see reproduction commit `685f1ad`.)
2. **Apply the minimal fix.** Replace the `redis.Redis(host=..., port=...)` construction with
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)`, using the config field that
   actually exists rather than inventing new ones.
3. **Re-run the new tests** and confirm all pass against the fixed code.
4. **Run the full unit suite** (`make test-unit`) and compare failure counts against a baseline
   with the fix reverted, to confirm no regressions are introduced elsewhere.
5. **Run `make check`** (ruff, black, mypy) scoped to the touched files, and note any pre-existing
   issues in those files separately from anything the fix introduces.

### Inputs & outputs

- **Input:** the `Settings` singleton (`core/config.settings`), specifically its `redis_url`
  field, which is populated from the `REDIS_URL` environment variable or the `.env` file.
- **Output:** the `/health` endpoint's JSON response — specifically
  `dependencies.redis` (`"healthy"` / `"unhealthy"`) and the overall `status` /
  HTTP status code, which should now reflect Redis's actual reachability instead of being
  permanently `"unhealthy"`.
- No API contract changes: the response shape is identical, only the *values* it reports change.

### Risks & unknowns

- **`from_url` parsing differences:** `redis.Redis.from_url` parses the DB index, username,
  password, and scheme (`redis://` vs `rediss://`) from the URL itself. The previous code
  hardcoded `db=0`. If `redis_url` in some environment encodes a different DB index (e.g.
  `redis://localhost:6379/1`), behavior will change from "always DB 0" to "whatever the URL
  says." I judge this to be the *correct* fix, not a regression, but it's worth flagging since
  it's a behavior change beyond just fixing the crash.
- **No live Redis in the dev/test environment.** All tests mock `redis.Redis.from_url` rather
  than hitting a real Redis instance, per the `unit` marker's "no external dependencies"
  contract. This means the fix is verified against the *interface* (the client is constructed
  and `ping()` is called) but not against a real Redis server. Integration-level verification
  would need Docker services (`make test-integration`), which I did not run.
- **Broad exception handling elsewhere in the same function.** The Postgres and vector-DB probes
  use the same broad `except Exception` pattern. This issue only fixes the Redis probe's root
  cause; the masking pattern itself is untouched and could hide a similar bug in those probes
  later. Out of scope for this issue, but worth a follow-up.

### Edge cases

- **Redis genuinely unreachable** (wrong host, server down, connection refused): `ping()` should
  raise, and the probe should still report `"unhealthy"` and return 503. Covered by
  `test_unreachable_redis_returns_503`, using a mocked `ConnectionError`.
- **Redis fully healthy alongside the other two dependencies:** the endpoint should return 200
  with `status: "healthy"`. Covered by `test_all_dependencies_healthy`.
- **`redis_url` missing or malformed:** not explicitly tested — `Settings` provides a default
  value, so this can't happen via normal config loading, but a malformed URL passed via
  environment variable would raise inside `from_url` and still be caught by the existing
  `except Exception`, degrading to `"unhealthy"` rather than crashing the endpoint. Existing
  behavior, not something this fix needs to change.
- **Config/consumer drift recurring:** `test_settings_defines_redis_url_not_host_port` asserts
  `Settings` has `redis_url` and does *not* have `redis_host`/`redis_port`, so if someone
  reintroduces the old fields (or the health check reverts to reading them) without updating the
  other side, this test fails immediately instead of the bug resurfacing silently.
