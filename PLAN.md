# Solution Plan

**Issue link:** [https://github.com/ascherj/pathreview/issues/82]

**Issue title:** [Concurrent review requests for the same profile can produce inconsistent results - #82]

## Issue Visualization

```mermaid
sequenceDiagram
    participant A as Request A<br/>process_review(profile_id=1)
    participant DB as Profile (shared state)
    participant B as Request B<br/>process_review(profile_id=1)

    A->>DB: 1. A_start: read Profile snapshot
    activate A
    Note over A: 2. A awaits mid-pipeline<br/>(ingestion -> orchestration, no lock held)
    B->>DB: 3. B_start: read Profile snapshot
    activate B
    Note over B: 4. B edits Profile, runs full pipeline
    B->>DB: 5. B commits changes
    B-->>B: 6. B_end: review complete
    deactivate B
    Note over A: 7. A resumes using STALE<br/>snapshot from before step 5
    A->>DB: 8. A commits changes (based on stale data)
    A-->>A: 9. A_end: review complete
    deactivate A

    Note over A,B: call_order = [A_start(1), B_start(3), B_end(6), A_end(9)]<br/>Result: inconsistent profile state<br/>Step 8 can silently overwrite or ignore step 5's edits
```

**What the diagram shows:** Request A begins first and holds an in-memory `Profile` snapshot across several `await` points (ingestion, orchestration, RAG, safety checks). Since nothing keys off `profile_id`, Request B is free to start, run to completion, and commit its own changes while A is still suspended mid-pipeline. When A eventually resumes and commits, it does so against its now stale snapshot, producing the interleaved `["A_start", "B_start", "B_end", "A_end"]` order the regression test asserts against. A per-profile lock would force B to wait until A releases the lock, guaranteeing one of the two non-interleaved orders instead.

## How to Reproduce

**Root cause:** `process_review()` in `core/services/review_service.py` fetches its own `Profile` snapshot, then runs a multi-step pipeline (ingestion → agent orchestration → RAG → safety checks) with several `await` points and `db.commit()` calls in between. Nothing keys off `profile_id` to prevent two calls from running concurrently, so two review requests submitted for the same profile close together interleave freely against shared profile state instead of being serialized.

The regression test at [`tests/integration/test_review_concurrency.py`](tests/integration/test_review_concurrency.py) pins this down deterministically (no flaky timing races) by monkeypatching the ingestion step of two concurrent `process_review()` calls to record when each starts/finishes, and forcing review A to pause mid-flight while review B's profile edit and full run land in between.

To reproduce it yourself, from the repo root:

```bash
# 1. Start the real Postgres the app uses (docker-compose.yml service is named `db`,
#    mapped to host port 5433)
docker compose up -d db

# 2. Point the app at it (matches .env.example)
export DATABASE_URL="postgresql+asyncpg://pathreview:pathreview@localhost:5433/pathreview_dev"

# 3. Apply migrations so the schema exists
make migrate

# 4. Run the regression test directly -- on unfixed code this FAILS
.venv/Scripts/pytest tests/integration/test_review_concurrency.py -v -m integration
```

(On macOS/Linux, use `.venv/bin/pytest` per the Makefile's `VENV_BIN` convention.)

**Expected result on current, unfixed code:** the test fails with

```
AssertionError: expected non-interleaved execution, got ['A_start', 'B_start', 'B_end', 'A_end']
```

## Understand

**Root cause:** `process_review()` in `core/services/review_service.py` fetches a `Profile` snapshot, then runs a multi-step pipeline (ingestion, agent orchestration, RAG, safety checks) with several `await` points and `db.commit()` calls in between. Nothing keys off `profile_id`, so two concurrent calls for the same profile interleave freely against shared profile state instead of being serialized.

**Expected behavior:** A second review request for a profile that already has a review in progress should wait for the first to finish before it starts, so the two loops never straddle each other.

**Actual behavior:** Both loops run concurrently. One loop can commit changes based on a stale snapshot read before the other loop's edits landed, producing inconsistent review results. The regression test at `tests/integration/test_review_concurrency.py` confirms this: on unfixed code, `call_order` comes back as `["A_start", "B_start", "B_end", "A_end"]` instead of one loop fully finishing before the other starts.

## Map

- `core/services/review_service.py`, `process_review()`: needs to acquire a per-profile Redis lock before running the pipeline and release it once the review reaches a terminal status (complete or failed).
- `core/services/review_service.py`, module level: needs a Redis client built from `settings.redis_url`, following the same pattern as `SessionStore` and `RateLimiter`, which both take a `redis.Redis` client already connected to the same instance.
- `core/config.py`: already exposes `redis_url`, no change needed there.
- `api/routes/reviews.py`, `create_review_endpoint()`: no change to endpoint response behavior. It already returns immediately with status "pending" and schedules `process_review` via `background_tasks.add_task`, so the lock only needs to live inside `process_review`, not the endpoint.
- `tests/integration/test_review_concurrency.py`: existing regression test, used as the pass/fail baseline for serialization. No changes expected to this file, since it only needs to keep passing under the new lock implementation.
- New test coverage (file and location still to be decided in Week 9): lock lifecycle in isolation, lock expiration, and what a second request observes while a lock is already held. See "Testing Strategy" below.

## Plan

I originally planned this fix around an in-memory `asyncio.Lock` registry. After getting feedback on my Week 7 submission, I am revising the plan to use a Redis backed lock with a TTL instead, since the codebase already depends on Redis for the session store and market analyzer, and an in-memory lock does not protect against a worker crashing while it holds the lock. The plan below reflects that revision. My prior `asyncio.Lock` plan and the reasoning behind it are kept further down in this file under "Prior iteration" so there is a record of how the design changed.

1. Add a module level Redis client in `review_service.py`, built from the existing `redis_url` setting in `core/config.py`, the same config value `SessionStore` and `RateLimiter` already read from.
2. At the start of `process_review()`, acquire a Redis lock keyed by `profile_id` with a TTL, using the `redis.asyncio` client's built in `lock()` helper rather than hand rolling `SET NX`. If the lock is already held, the call blocks until it is released or the TTL expires.
3. Wrap the same span of `process_review()` that the original plan called out (from status set to "processing" through the terminal status commit) so the lock covers the full pipeline, not just one step.
4. Release the lock on every exit path, including the existing exception handler that marks the review "failed", and treat a release against an already expired lock as a non fatal, logged event rather than a crash, since expiry is the intended safeguard, not a bug.
5. Write the new tests called out in "Testing Strategy" below for the lock lifecycle, expiration, and contention, since the existing regression test only proves serialization under the happy path.
6. Run the regression test against the fix and confirm `call_order` comes back as one of the two non-interleaved orders.
7. Run `make check` and `make test-unit` per CONTRIBUTING.md before opening the PR.

## Fix Visualization

```mermaid
sequenceDiagram
    participant A as Request A<br/>process_review(profile_id=1)
    participant L as [FIX] Redis Lock<br/>[FIX] review_lock:1
    participant DB as Profile (shared state)
    participant B as Request B<br/>process_review(profile_id=1)

    A->>L: [FIX] 1. A acquires lock (timeout=300)
    activate L
    A->>DB: 2. A_start: read Profile snapshot
    activate A
    Note over A: 3. A awaits mid-pipeline<br/>(ingestion -> orchestration, [FIX] lock held)
    B->>L: [FIX] 4. B attempts acquire, BLOCKS<br/>[FIX] (lock already held for profile_id=1)
    Note over B: [FIX] 5. B waits...
    A->>DB: 6. A commits changes
    A-->>A: 7. A_end: review complete
    deactivate A
    A->>L: [FIX] 8. A releases lock (finally block)
    deactivate L
    L->>B: [FIX] 9. B acquires lock
    activate L
    B->>DB: 10. B_start: read Profile snapshot<br/>[FIX] (fresh, post-A-commit state)
    activate B
    Note over B: 11. B runs full pipeline
    B->>DB: 12. B commits changes
    B-->>B: 13. B_end: review complete
    deactivate B
    B->>L: [FIX] 14. B releases lock (finally block)
    deactivate L

    Note over A,B: call_order = [A_start(2), A_end(7), B_start(10), B_end(13)]<br/>[FIX] Result: consistent profile state<br/>[FIX] B always reads state that reflects A's completed commit
```

**What the diagram shows:** The Redis lock, keyed as `review_lock:{profile_id}`, is acquired before the `Profile` snapshot is read and held across the entire pipeline span. Request B's acquire attempt blocks instead of proceeding while A still holds the lock. So, B cannot start until A has fully committed and released. This guarantees one of the two non-interleaved orders, and B's snapshot always reflects A's completed changes rather than a stale one. The lock is released in a finally block on every exit path, including failure. So, a crashed or errored pipeline doesn't hold it beyond the release call, and the TTL is the backstop if release itself never runs.

## Inputs & Outputs

Input: the existing regression test's two concurrent `process_review()` calls for the same `profile_id`, one slowed down mid-ingestion to simulate real fetch latency, the other editing the profile and submitting while the first is still in flight.

Output: `call_order` must equal `["A_start", "A_end", "B_start", "B_end"]` or `["B_start", "B_end", "A_start", "A_end"]`, per the "Expected result once fixed" section in JOURNAL.md. No change to the review's external API contract, `create_review_endpoint()` still returns "pending" immediately.

## Risks, Unknowns, and Limitations

The biggest risk with my original `asyncio.Lock` plan was that it only serializes within a single worker process. Moving to a Redis lock removes that limitation for free, since Redis is a shared, out of process store the app already depends on. So, the lock now holds across multiple worker processes and machines, not just a single process. This also means the "single-process only" limitation from my original plan no longer applies and can be dropped.

The main new risk with a Redis lock is a crashed or stuck worker holding the lock forever with no one left to release it (deadlock). A TTL is the safeguard: the lock expires on its own after a fixed window even if the process holding it dies mid-pipeline, so a later request for the same profile is never permanently blocked. The TTL needs to be comfortably longer than a real review pipeline takes to run, or the lock could expire while a healthy request is still legitimately using it, letting a second request start too early. I still need to pick and justify a concrete TTL value once I can measure how long the real pipeline takes end to end.

A second risk is a surface level patch that only satisfies the test's exact timing without actually serializing the pipeline, for example locking only around the ingestion step instead of the whole pipeline. The lock needs to wrap the entire `process_review` body so downstream agent orchestrator state for a given profile is never touched by two runs at once.

A third risk, called out directly in the feedback I received, is only testing the happy path where the lock is acquired, the work runs, and the lock is released cleanly. That alone would miss regressions in how the lock behaves when it is already held or when it expires. The Testing Strategy section below is my plan for covering those cases too.

## Edge Cases

Verify the fix holds as the two loops' timing windows narrow toward zero overlap, not just the specific 0.2s and 0.05s sleep values in the current test, since the lock should serialize regardless of exact timing.

Verify what a second request actually observes while a lock is already held for its profile_id, since this is the exact scenario called out in my feedback. It should block and wait rather than proceeding, and once it does proceed, it should not be operating on stale state from before the first request's commit.

Verify lock expiration behaves correctly: if a lock's TTL elapses without an explicit release (simulating a crashed worker), a second request for the same profile must be able to acquire the lock rather than waiting forever.

Verify the lock is released even when the pipeline raises partway through, covered by the existing try/except in `process_review`. A failed pipeline run should not leave the lock held until its TTL expires if it can be released immediately instead.

Confirm a third, fourth, etc. concurrent request for the same profile queues correctly rather than just the two request case the current regression test covers.

## Testing Strategy

The existing regression test at `tests/integration/test_review_concurrency.py` only proves the happy path: lock acquired, pipeline runs, lock released, in the right order. Per the feedback on my Week 7 submission, I am planning to add tests that cover the lock mechanism itself in isolation, not just the end to end pipeline behavior:

1. **Lock lifecycle test:** acquire the lock, do some work, release it, and confirm it is actually gone from Redis afterward. This does not need real concurrency to be useful, a sequential test that exercises acquire then release will already catch most regressions in the lock code itself.
2. **Lock expiration test:** acquire the lock, do not release it, wait past the TTL (or use a short TTL just for the test), and confirm a second acquire attempt succeeds instead of blocking forever.
3. **Contention test:** acquire the lock, then attempt a second acquire while the first is still held, and confirm the second attempt blocks or fails to acquire immediately, rather than silently succeeding and letting two callers hold the same profile's lock at once.

These will live alongside or near `tests/integration/test_review_concurrency.py` once I start implementation in Week 9. I have not written them yet since Week 8 is reproduction and planning only, but I wanted my plan to name concretely what "test coverage" means here instead of leaving it as a vague follow up.

## Prior iteration (kept for traceability)

My first pass at this plan (see the reproduction commit and my Week 7 JOURNAL.md entry) proposed a plain `asyncio.Lock` registry: a module level dict mapping `profile_id` to an `asyncio.Lock`, created lazily and reused across calls, with `process_review()` wrapped in `async with` the profile's lock. That version is superseded by the Redis based design above, but I am keeping the original reasoning here rather than deleting it, since it documents why I changed course:

- The `asyncio.Lock` approach is simple stdlib and needs no new dependency, but it only works within a single process, which was flagged as a known, out of scope limitation rather than something I intended to fix.
- I got feedback pointing out that the codebase already uses Redis (visible in the session store and market analyzer) and that a lock with no TTL has no defense against a crashed process holding it forever. That is the direct reason for the switch to a Redis lock with a TTL.
- The original plan also only called for testing the non-interleaved happy path via the existing regression test, without separate coverage for lock expiration or contention. The Testing Strategy section above is the response to that gap.
