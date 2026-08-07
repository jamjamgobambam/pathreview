## Solution plan

**Issue:** Health check references `settings.redis_host`, which does not exist on Settings — https://github.com/ascherj/pathreview/issues/155

### Understand

The root cause is a config mismatch: `api/routes/health.py`'s Redis check
constructs its client with `settings.redis_host` and `settings.redis_port`,
but the `Settings` class (`core/config.py`) only defines `redis_url` — those
two fields have never existed. Because the check is wrapped in a broad
`except Exception`, the resulting `AttributeError` is silently caught and
reported as `"redis": "unhealthy"` instead of surfacing as a crash.

**Expected behavior:** `/health` should report Redis's real connection status.
**Actual behavior:** `/health` reports `"redis": "unhealthy"` on every single
call, regardless of whether Redis is actually running — a permanent false
negative.

### Map

Files involved:
- `api/routes/health.py` — contains the buggy Redis check (the only file that
  needs a code change)
- `core/config.py` — defines `Settings`; read-only for this fix, confirms
  `redis_url` is the only Redis field that exists
- `tests/unit/test_health_routes.py` — new file, since no test currently
  exists for this route

I confirmed via `grep -rn "redis.Redis(\|redis_url" .` that no other file in
the codebase constructs a raw `redis.Redis` client or references host/port
config — `health.py` is the only place this pattern appears, and `redis_url`
is the only config value used anywhere else. This ruled out inventing new
`redis_host`/`redis_port` fields as the fix.

### Plan

1. Reproduce the bug live: start the full stack (`make run`), confirm Redis
   is genuinely healthy via `docker compose ps`, then hit `/health` and
   observe the false "unhealthy" report along with the exact `AttributeError`
   in the server logs.
2. Replace the client construction in `health.py`'s Redis check with
   `redis.Redis.from_url(settings.redis_url, decode_responses=True)`,
   matching the one config field that actually exists.
3. Re-verify against the live server: confirm `/health` now reports
   `"redis": "healthy"`.
4. Write `tests/unit/test_health_routes.py` — the first route-level test in
   this codebase — covering both the healthy path (mocked Redis ping
   succeeds) and the genuinely-unhealthy path (mocked Redis ping fails).
5. Run the full test suite and lint/type checks; confirm via a `git stash`
   comparison that no new failures are introduced beyond this codebase's
   pre-existing debt.

### Inputs & outputs

**Input:** An HTTP `GET /health` request.
**Output before fix:** JSON body reporting `"redis": "unhealthy"` (false, a
503 status) regardless of Redis's actual state.
**Output after fix:** JSON body correctly reflecting Redis's real
connectivity — `"healthy"` when Redis is reachable, `"unhealthy"` only when
a real connection failure occurs.

### Risks & unknowns

- **No existing test pattern for FastAPI routes in this codebase** — every
  existing test targets a service/utility class directly, with no
  `TestClient` or `get_db` dependency-override pattern to copy. Risk:
  building this pattern incorrectly could produce a test that looks right
  but doesn't actually exercise the real route. Mitigated by verifying the
  test actually fails when the old buggy code is reintroduced (confirmed by
  testing against the original code via `git stash`).
- **Pre-existing repo-wide test/lint debt** — the full suite has 53
  pre-existing failures and the `mypy`/`ruff` pre-commit hooks flag ~48
  unrelated errors across files I never touched. Risk: mistakenly believing
  my change caused a regression, or conversely trying to fix unrelated debt
  and blowing past Tier-1 scope. Mitigated with a `git stash` before/after
  comparison to isolate exactly what's mine.
- **Issue #154 lives in the same function** (a separate raw-SQL-string bug
  affecting the Postgres check) — risk of scope creep by "fixing it while
  I'm in there." Deliberately stayed scoped to #155 only.

### Edge cases

- Redis genuinely unreachable (real connection failure, not a config bug) —
  should still report `"unhealthy"`, not be masked by the fix. Covered by
  the second test case.
- Redis reachable but slow/timing out — outside this issue's scope (the fix
  doesn't change timeout behavior, only the client construction).
- `redis_url` itself malformed or missing from `.env` — would still raise an
  exception, still correctly caught by the existing `except` block and
  reported as unhealthy; not a new failure mode introduced by this fix.