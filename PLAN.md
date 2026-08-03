# Solution plan

**Issue:** [#82 — Concurrent review requests for the same profile can produce inconsistent results](https://github.com/ascherj/pathreview/issues/82)

### Understand

**Root cause:** `POST /reviews` has no per-profile serialization. Two overlapping requests both create a `Review` and both drive `process_review` through ingestion / agent / RAG / safety against the same profile state, interleaving reads and writes.

**Expected:** concurrent reviews for the same profile produce consistent, non-conflicting results — the final `Review` state reflects one coherent run, not two overlapping ones. The issue doesn't prescribe *how* (reject vs queue vs merge); that's a design decision — see below.

**Actual (reproduced in [`6daedb7`](https://github.com/ascherj/pathreview/commit/6daedb7)):** two concurrent creates both succeed, both complete, profile ends up with two `complete` reviews from overlapping runs with last-writer-wins commits.

### Serialization: where and how

**Design decision — reject, don't queue.** Two ways to prevent overlap: (A) reject the second request with 400, or (B) queue it server-side until the first finishes. Chose **A** — matches the existing `POST /auth/register`-returns-400 convention, and a full review is too long to reasonably hold an HTTP connection open waiting. Queue-and-wait would need `202 Accepted` + polling / SSE machinery for the same correctness guarantee.

**Where:** in `create_review_endpoint`, before any `Review` row is written — otherwise the race window just moves.

**How:** Redis `SET review_lock:{profile_id} <token> NX EX 300` for atomic acquire; Lua compare-and-delete against the per-request token for safe release (so a stale owner whose TTL fired can't delete a fresh holder's key). Release runs in the background task's `finally`. Redis over an in-process `asyncio.Lock` because a per-process lock silently breaks across workers/replicas.

### Map

Files touched:
- `api/routes/reviews.py` — acquire at the top of `create_review_endpoint`; release wrapped around the background task.
- `core/redis_client.py` *(new)* — cached `redis.asyncio` client provider.
- `core/services/review_lock.py` *(new)* — `ReviewLock` primitive.
- `tests/unit/test_review_lock.py` *(new)* — primitive tests.
- `tests/unit/test_reviews_race.py` *(already committed in `6daedb7`)* — endpoint-level regression, flips green when the lock lands.

**Not touched** (out of scope per the reviewer): `core/services/review_service.py` (session-leak + stale-`review`-across-awaits bugs).

### Plan

1. Add `core/redis_client.py` — `get_redis_client()` returning an `lru_cache`d `redis.asyncio` client.
2. Add `core/services/review_lock.py` — `ReviewLock(redis, profile_id, ttl_seconds=300)` with `acquire()` (SET NX EX) and `release()` (Lua compare-and-delete, swallows Redis errors).
3. Wire into `create_review_endpoint`: acquire → on failure raise `HTTPException(400, "A review for this profile is already in progress")`; on success create the review and hand the background task a `_process_and_release()` wrapper that releases in `finally`. Release on the create-time error path too.
4. Add primitive tests for `ReviewLock` (acquire, contention, release token match, error tolerance).
5. Confirm `test_reviews_race.py` flips green.

### Inputs & outputs

**Input:** existing `POST /reviews` payload (`profile_id`) — no schema change.

**Outputs:**
- First request → unchanged (200, pending review, background task).
- Second concurrent request for the same profile → `HTTPException(400, "A review for this profile is already in progress")`.
- After the first completes / crashes and TTL expires → next request behaves like the first again.

**New side effect:** one Redis key per active review (`review_lock:{profile_id}`, 300s TTL), deleted at background-task teardown.

### Risks & unknowns

- **TTL vs review duration.** 300s is comfortably longer than the current mock pipeline; if the real pipeline exceeds it, a second create could slip through. TTL is a knob, not a hard fix. No refresh/renewal in this PR.
- **Redis outage.** `acquire()` propagates → 500 via the existing catch-all. Stricter than `RateLimiter`'s fail-open, but fail-open here would silently reintroduce the bug. Worth flagging to the reviewer.
- **Not load-tested against real Redis.** Primitive tests use an in-process fake honoring `SET NX EX` + `EVAL`. Spot-check against `pathreview-redis-1` before opening the PR.
- **Adjacent bug flagged on the thread** (`_run_ingestion_pipeline` never persists `IngestedSource` rows) is unrelated to the lock and stays out of scope.

### Edge cases

- **Same profile, different users** → still serialized (key is `profile_id`; profile state is shared).
- **Different profiles, same user** → no contention (independent keys).
- **`create_review` raises after acquire** → released in the error path (no 300s hang).
- **`process_review` raises** → `try/finally` still releases.
- **Redis dies mid-review** → `release()` swallows the error; key auto-expires; the review still completes.
- **Rapid retries after 400** → each is one cheap `SET NX`. Rate limiting is the right layer for pushback, not the lock.
