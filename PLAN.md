# Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155) (#155)

## Understand

**Root cause.** The `/health` handler builds its Redis client from two settings fields
that were never defined:

```python
# api/routes/health.py:44-49
r = redis.Redis(
    host=settings.redis_host,   # does not exist
    port=settings.redis_port,   # does not exist
    db=0,
    decode_responses=True,
)
```

`Settings` in `core/config.py` defines only `redis_url` (line 12, default
`redis://localhost:6379/0`). There is no `redis_host` and no `redis_port`. The attribute
lookup raises `AttributeError` before any network call is attempted, and the enclosing
`except Exception` catches it and marks the dependency `"unhealthy"`.

The failure is deterministic — it happens on every request, and it never depends on
whether Redis is actually running.

**Expected vs. actual.**

| | Redis running | Redis stopped |
|---|---|---|
| Expected | `redis: "healthy"` | `redis: "unhealthy"` |
| Actual | `redis: "unhealthy"` | `redis: "unhealthy"` |

Verified locally (see JOURNAL.md, Week 8): `docker compose exec redis redis-cli ping`
returns `PONG` while `GET /health` returns 503 with `redis: "unhealthy"`. The server log
confirms the cause:

```
redis_health_check_failed  error="'Settings' object has no attribute 'redis_host'"
```

The deeper problem is that the broad `except Exception` makes a coding error
indistinguishable from a real outage — both produce identical output, which is why this
shipped unnoticed.

## Map

**Files I expect to touch:**

| File | Change |
|---|---|
| `api/routes/health.py` | Replace the Redis client construction in `health_check` (lines 44–49) |
| `tests/unit/test_health.py` | **New file** — first tests for the health route |

**Files I need to understand but will not modify:**

| File | Why |
|---|---|
| `core/config.py` | Source of `redis_url`; confirms `redis_host`/`redis_port` do not exist |
| `tests/conftest.py` | Shared fixtures; may need a client fixture added |
| `core/database.py` | Provides the `get_db` dependency I must override in tests |

**Blast radius.** `health.py` is the only place in the codebase that constructs a Redis
client. `RateLimiter` accepts an injected client and is never instantiated in production
code, so no other module depends on the broken pattern. The change cannot affect the
Postgres or vector-DB branches of the handler.

## Plan

1. **Fix the client construction.** Replace the `redis.Redis(host=..., port=...)` call
   with `redis.Redis.from_url(settings.redis_url, decode_responses=True)`. Already
   validated against the running container — it returns `ping() -> True`. Also drop the
   explicit `db=0` as redundant, since the database index is carried in the URL path.
   (Verified: redis-py lets the URL's index win over a `db=` kwarg, so keeping it would
   not actually cause a bug — removing it is a readability tidy-up, not a fix.)

2. **Add `tests/unit/test_health.py`.** No route tests exist anywhere in this repo, so
   this establishes the pattern. Cover three cases: Redis reachable → `"healthy"`; Redis
   raising `ConnectionError` → `"unhealthy"`; and a regression guard asserting the client
   is built from `redis_url` rather than any host/port attribute. Patch `redis.Redis` and
   override the `get_db` dependency so the test stays a true unit test with no Docker
   requirement (`-m unit` must remain fast and dependency-free).

3. **Verify the real behavior end to end.** With Docker up, confirm `redis` flips to
   `"healthy"` in the live response. Then stop the Redis container and confirm it
   correctly reports `"unhealthy"` — proving the probe now distinguishes the two states
   instead of always failing.

4. **Run the full gate.** `make check && make test-unit`. Note that `make check` runs
   mypy; `types-redis` is already in dev dependencies, so `from_url` should type-check
   cleanly.

5. **Open the PR, then file follow-ups.** Fill out `.github/PULL_REQUEST_TEMPLATE.md`,
   `Closes #155`, and flag the out-of-scope findings for reviewers (see Risks below).
   Open separate issues for the Postgres `text()` bug and the two pre-existing Redis
   weaknesses rather than folding them into this change.

## Inputs & outputs

**Input:** `settings.redis_url` — a Redis connection URL string sourced from the
`REDIS_URL` environment variable or `.env`, defaulting to `redis://localhost:6379/0`.

**Output:** the `dependencies.redis` field of the `GET /health` response body, which
becomes `"healthy"` or `"unhealthy"` based on whether `PING` actually succeeds, plus its
contribution to the top-level `status` and the 200/503 status code.

**Behavioral change:** the Redis probe performs a real network round-trip instead of
raising `AttributeError`. Nothing about the response *schema* changes — the same keys with
the same types. Only the correctness of one value changes.

## Risks & unknowns

**The endpoint will still return 503 after this fix.** The Postgres probe on line 31
calls `await db.execute("SELECT 1")` with a raw string, which SQLAlchemy 2.x rejects
(`Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`).
So `dependencies.redis` will correctly flip to `"healthy"`, but `status` stays
`"unhealthy"` and the code stays 503 until that separate bug is fixed. This is the
biggest risk of the PR being misread as "not working." I will state it explicitly in the
PR description and file a separate issue rather than expanding scope.

**Two pre-existing weaknesses, noted but out of scope.** Neither is caused by this fix
and neither will be changed here — both are worth their own issues:

- *No connection timeout.* Without `socket_connect_timeout`, a `redis_url` pointing at an
  unreachable-but-routable host makes the probe hang for the OS default, which would hang
  the health endpoint itself.
- *No connection cleanup.* Each request builds a new client and never closes it; a pooled
  module-level client would be the sturdier pattern.

I will mention both briefly in the PR and open follow-up issues rather than widening this
change.

**Test-pattern risk.** Being the first route test in the repo, my fixture approach has no
precedent to copy and may not match what maintainers want. Mitigation: keep it minimal
and idiomatic, and be ready to restructure on review feedback.

**Low risk of regression.** The change is one expression inside one `try` block, in the
only Redis construction site in the codebase.

## Edge cases

The fix should handle these gracefully — all of them are handled by `from_url` parsing
the URL, which is precisely what the hand-rolled host/port construction could not do:

| Case | Expected behavior |
|---|---|
| `redis://localhost:6379/0` (default) | Connects, reports `"healthy"` |
| URL with a non-zero DB index (`/2`) | Honors the index from the URL (verified: resolves to db 2) |
| URL with credentials (`redis://:pw@host:6379/0`) | Authenticates from the URL |
| TLS scheme (`rediss://`) | Handled by `from_url`; the old code could not express this at all |
| Redis genuinely down | Reports `"unhealthy"` and 503 — the true-negative case, explicitly tested |
| Malformed `redis_url` | `from_url` raises `ValueError`, caught by the existing `except`, reported `"unhealthy"` |
| Empty `redis_url` | Same as malformed — reported `"unhealthy"` rather than crashing the endpoint |

Note that the last two cases report a *configuration* error as a *dependency* outage.
That is the same conflation that hid this bug, but narrowing the exception handling is
out of scope for #155 and belongs in its own issue.
