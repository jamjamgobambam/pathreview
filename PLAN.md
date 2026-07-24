## Solution plan

**Issue:** [Concurrent review requests for the same profile can produce inconsistent results](https://github.com/ascherj/pathreview/issues/82)

### Understand
When two review requests are submitted simultaneously for the same profile, both agent loops run against the same `Profile` state. The second loop can read stale data modified by the first, producing inconsistent review results. The expected behavior is that reviews for the same profile should be serialized so each one sees a consistent, up-to-date state.

### Map
Files involved:
- `core/services/review_service.py` — processes reviews in the background (`process_review`)
- `api/routes/reviews.py` — endpoint that creates reviews and triggers background processing
- `core/database.py` — `get_db` dependency that yields request-scoped DB sessions

Functions involved:
- `create_review_endpoint` — kicks off background task
- `process_review` — background task that runs ingestion, agent, RAG, safety
- `_process_review_impl` — actual review processing logic (added during fix)

### Plan
1. Extend `_process_review_impl` to accept a Redis-backed `redis.asyncio.Lock` keyed by `profile_id` so the lock survives across worker processes.
2. In `process_review`, acquire the per-profile lock before calling `_process_review_impl`.
3. (Optional, same PR) Return HTTP 400 from `create_review_endpoint` when a review is already in-flight for that profile, matching the existing auth convention.
4. Add unit tests in `tests/unit/test_review_service.py` to verify two concurrent `process_review` calls are serialized.

### Inputs & outputs
- Input: `review_id` (UUID), `profile_id` (UUID), DB session `db`
- Output: Review status transitions from `pending` → `processing` → `complete` or `failed`; sections and score stored on success
- Side effect: Redis lock key `review:lock:{profile_id}` held for the duration of processing

### Risks & unknowns
- Redis lock TTL must be long enough for slow ingestions; too short risks premature release, too long risks stuck locks on crashes.
- `BackgroundTasks` shares the same event loop; if the app moves to a task queue (Celery/RQ), the in-process lock registry becomes invalid — a Redis lock mitigates this.
- Shared DB session between request and background task is an adjacent gap (noted by reviewer); fixing it is out of scope for this PR but could affect lock reliability if sessions are closed mid-run.

### Edge cases
- Two rapid POSTs for the identical profile_id should not run agent loops concurrently.
- Lock is released correctly even if `_process_review_impl` raises an exception.
- Different profiles can be reviewed concurrently (lock is per-profile, not global).
- A crashed/restarted worker should not deadlock the lock indefinitely (TTL or explicit release).
