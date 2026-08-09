# Implementation steps — per-profile lock (issue #82)

Working notes for actually implementing the fix, more granular than PLAN.md's high-level plan. No code has been written yet — this is the sequencing and reasoning only.

## 1. Add the async Redis client (new file)

A new small module, `core/redis_client.py`, mirroring how `core/database.py` already does it for Postgres: a module-level singleton created once via `redis.asyncio.Redis.from_url(settings.redis_url)`. Kept separate from the existing sync `redis.Redis` usage (`RateLimiter`, `SessionStore`, `health.py`) rather than touching those — they're fine as-is for their quick, occasional calls; this is a new, different usage pattern (a held-open lock) that specifically needs the async client.

## 2. Pick a lock key namespace

`f"profile-lock:{profile_id}"` — checked against the existing key prefixes in this codebase (`rate_limit:{identifier}` in `rate_limiter.py`, `session:{session_id}` in `session_store.py`) — no collision.

## 3. Restructure `process_review()`'s exception handling into two layers

The one real structural subtlety. Right now there's a single `try/except` (lines 98–194 of `core/services/review_service.py`) that catches anything that goes wrong *during* processing. Per the fail-closed decision, a failure to *acquire the lock in the first place* (Redis unreachable) needs its own handling — it happens before we'd even enter that existing try block, and it's a different failure mode (couldn't get a green light to run at all, vs. something broke while running). So:

- **Outer layer:** attempt `redis_client.lock(key, timeout=60)` acquisition. If that itself raises, log `profile_lock_acquire_failed` with `profile_id` and the error, mark the review `"failed"`, and stop — this is the new fail-closed path.
- **Inner layer:** the existing try/except (lines 98–194), now living entirely inside the `async with` block, unchanged in its own logic.

## 4. Distinguish two different timeout knobs on the lock

`redis.asyncio`'s `Lock` has two separate parameters, worth being deliberate about rather than only setting one:

- `timeout=60` — how long *my own* hold lasts before Redis auto-expires it (the TTL already decided on).
- `blocking_timeout` — how long `.acquire()` keeps retrying against an *already-held* lock before giving up. Left at its default (block indefinitely), since a waiting review is *supposed* to wait for however long the first one takes — that's the entire point of this fix, not something to time out on.

## 5. Test infrastructure gap — needs a Redis testcontainer

Real gap the tests don't currently cover: `tests/conftest.py`'s `pytest_configure` only spins up an ephemeral Postgres container. Once `process_review()` actually calls into Redis for real, the integration tests need a reachable Redis too, or they'll fail for an unrelated reason (no Redis running) rather than testing the lock behavior. Same pattern as the Postgres container: start an ephemeral `redis:7-alpine` testcontainer, point the relevant Redis URL setting at it before `core.config` is first imported, tear down at session end.

## 6. Confirm the two existing tests still pass unmodified

They assert on observable behavior (windows don't overlap, other review's status is already terminal) via patching `_run_ingestion_pipeline`, not on the lock's implementation — so they should just start passing once the real lock exists, no test changes needed. Worth explicitly verifying this rather than assuming it.

## 7. Add the new exception-path test

A review that raises partway through (patch e.g. `_run_agent_orchestration` to raise for review 1) must still release its profile's lock — verified by confirming review 2 (same profile) proceeds and completes shortly after, rather than hanging.

## 8. Add the new Redis-unreachable test

Point the async client at an unreachable address (or patch the lock's `acquire` to raise), and confirm: review ends up `"failed"`, and the `profile_lock_acquire_failed` log line fires.

## 9. Sequencing

Steps 1–4 (the actual fix) before 5–8 (test infra + new tests) doesn't quite work in practice — the Redis testcontainer (step 5) needs to be in place *before* running steps 6–8 against real infrastructure. Practical order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.
