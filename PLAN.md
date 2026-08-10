## Solution plan

**Issue:** [Add a safety event count to the health check endpoint (#68)](https://github.com/ascherj/pathreview/issues/68)

### Understand

**Root cause:** `api/routes/health.py`'s `health_check()` hardcodes the
`safety_events_last_hour` field to `0` in two places — once in the initial
`health_status` dict (currently line 21) and again inside a no-op `try` block
(currently lines 71-74) whose comment literally says "This would be populated
by actual safety event logging." Meanwhile, `safety/monitoring.py` already
has a working `SafetyMonitor` class: `log_event()` increments a per-event-type
Redis counter (`safety:events:{event_type}`, keys expire after 24h) whenever
the safety layer catches something, and `get_event_count(event_type,
window_hours=1)` reads that counter back. Nothing in the codebase ever
constructs a `SafetyMonitor` or calls `get_event_count()` — confirmed via a
repo-wide grep for `SafetyMonitor(`, which returned zero production call
sites.

**Expected vs. actual behavior:**
- Expected: `GET /health` reports how many real safety events (PII
  detections, injection attempts, content filtering, bias flags, rate
  limiting) occurred in the last hour.
- Actual: the field always reads `0`, regardless of how many real events
  `SafetyMonitor.log_event()` has recorded in Redis. I confirmed this with a
  reproduction test (`tests/unit/test_health.py`, committed in `823a04d`)
  that seeds a mocked Redis client with a `pii_detected` count of 5 and
  asserts the health response reflects it — the assertion fails with
  `0 != 0`.

### Map

Files I expect to touch for the actual fix (Week 9+):

- `api/routes/health.py` — replace the hardcoded `0` with real calls into
  `SafetyMonitor`; add a Redis dependency to the route.
- `safety/monitoring.py` — no logic changes expected, but may need a small
  addition (e.g. a "sum across all event types" helper) depending on how the
  aggregation question below gets resolved.
- `core/database.py` — reference pattern only (not modified): its
  `get_db()` async-generator + `Depends()` dependency is the closest existing
  convention in the repo for what a `get_redis()` dependency should look
  like, since no Redis DI pattern exists yet anywhere in the app.
- Possibly a new `core/redis.py` (or similar) to hold a `get_redis()`
  dependency, since every current Redis consumer (`safety/rate_limiter.py`,
  `safety/monitoring.py`, `agent/memory/session_store.py`) takes a
  `redis_client` constructor argument but nothing in production code
  actually constructs one — I'd be establishing the first instance of this
  pattern, not extending an existing one.
- `core/config.py` — the Redis health check block a few lines above the
  bug (currently lines ~44-51) references `settings.redis_host` /
  `settings.redis_port`, but `Settings` only defines `redis_url`. This is a
  second, pre-existing bug in the same function (confirmed: it raises
  `AttributeError`, silently caught, marking Redis "unhealthy" every time).
  Fixing the real issue needs a working Redis client anyway, so I'll likely
  need to touch this too — probably via `redis.Redis.from_url(settings.redis_url)`
  instead of the host/port fields.
- `tests/unit/test_health.py` — the reproduction test I already wrote will
  need to flip from "fails, proving the bug" to "passes, proving the fix,"
  plus new edge-case tests (see below).

### Plan

1. **Resolve the aggregation question** — should `safety_events_last_hour`
   be one summed count across all `SafetyMonitor.VALID_EVENT_TYPES`, or a
   per-type breakdown dict? I flagged this as unresolved back in the Week 7
   journal entry. Before writing the fix, check the issue #68 thread for
   maintainer guidance; if none exists, default to a summed integer (matches
   the field's singular, non-plural name) and document that judgment call
   in the PR description.
2. **Add a `get_redis()` dependency** modeled on `core/database.py`'s
   `get_db()` pattern, and use it to also fix the dead
   `redis_host`/`redis_port` reference in the existing Redis health check
   (switch to `redis.Redis.from_url(settings.redis_url)`).
3. **Wire `SafetyMonitor` into `health_check()`** — construct it with the
   injected Redis client, loop over `VALID_EVENT_TYPES` calling
   `get_event_count(event_type)`, sum (or structure per the decision in
   step 1), and replace the hardcoded `0`.
4. **Flip `tests/unit/test_health.py` to green** and extend it with the
   edge cases below; add a small unit test for whatever aggregation helper
   step 3 introduces.
5. **Run `make check && make test-unit`** locally before opening the PR, per
   `docs/CONTRIBUTING.md`'s PR checklist, and confirm `docker compose up -d`
   + a manual `curl localhost:8000/health` shows a real count end-to-end.

### Inputs & outputs

- **Input:** Redis keys of the form `safety:events:{event_type}` for each of
  the five `VALID_EVENT_TYPES`, written by `SafetyMonitor.log_event()`
  elsewhere in the safety pipeline.
- **Output:** an accurate `safety_events_last_hour` value in the `/health`
  endpoint's JSON response — either a single summed integer or a per-type
  breakdown object, depending on the step-1 decision — that changes as real
  events are logged, instead of an unconditional `0`.

### Risks & unknowns

- **Dead `redis_host`/`redis_port` settings bug** (`core/config.py` only has
  `redis_url`) means the existing Redis health check silently fails today;
  I can't test a real end-to-end fix without addressing this too, which
  slightly expands the diff beyond "just wire up SafetyMonitor."
- **No prior Redis DI pattern to copy exactly** — I'm introducing the first
  `get_redis()`-style dependency in the app, so there's room to over- or
  under-engineer it. I'll keep it as close to `get_db()`'s shape as
  possible rather than designing something new.
- **`get_event_count()`'s `window_hours` param is documented as "not
  enforced here; for reference"** while `log_event()` sets a 24-hour Redis
  TTL — so "last hour" in the field name may already be misleading even
  after the fix (a count from 23 hours ago would still show up). I'll flag
  this rather than silently expanding scope to fix TTL-based windowing,
  since that's arguably a separate issue.
- **Aggregation-shape ambiguity** (sum vs. per-type breakdown) is a genuine
  open product decision, not just an implementation detail — if I guess
  wrong, the PR may need rework after review.
- Repo-wide mypy/ruff strictness (`disallow_untyped_defs`, ruff's B008 rule
  against `Depends()` in argument defaults) means any route I touch needs
  full type annotations — I already hit this while committing the
  reproduction test and had to add `Annotated[AsyncSession, Depends(get_db)]`
  typing to `health_check()` to get pre-commit hooks passing.

### Edge cases

- Redis is unreachable — the health check should still return a response
  (dependencies.redis = "unhealthy") rather than raising an unhandled
  exception that 500s the whole endpoint.
- No safety events have ever been logged — `get_event_count()` should
  return `0` cleanly (it already does, via its own `except` fallback), not
  be confused with the current *always*-`0` bug.
- A Redis key has expired (past its 24h TTL) between when an event was
  logged and when `/health` is polled — count should just drop back to `0`
  for that event type, not error.
- All five `VALID_EVENT_TYPES` have non-zero counts simultaneously — the
  summing (or breakdown) logic needs to handle all of them, not just the
  one type exercised by the current reproduction test.
