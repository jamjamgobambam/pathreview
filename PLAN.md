## Solution plan

**Issue:** Concurrent review requests for the same profile can produce inconsistent results — [ascherj/pathreview#82](https://github.com/ascherj/pathreview/issues/82)

### Understand

**Expected behavior:** Only one review should ever be "in progress" for a given `profile_id` at a time. If a second request comes in while one is running, it should either be rejected/queued, or return the in-flight review's eventual result — never start a second, independent pass.

**Actual behavior:** `create_review()` in `core/services/review_service.py` has no check for an existing in-flight review before starting a new one. Two near-simultaneous requests for the same `profile_id` each independently call `process_review()`, which re-runs `_run_ingestion_pipeline()`. This produces:
- two `IngestedSource` rows for the same profile (duplicate ingestion), and
- two competing `Review` rows, with no way for the client to know which one is authoritative.

**Root cause:** Missing concurrency guard at the entry point (`create_review()`) — there is no per-profile lock, no unique constraint, and no "reject if in-flight" check before the pipeline starts.

### Map

Files/functions expected to change:
- `core/services/review_service.py`
  - `create_review()` — add the guard/lock check before dispatching to `process_review()`
  - `process_review()` — release the lock/mark the review complete when finished (including on failure)
- `api/routes/reviews.py`
  - `POST /reviews` handler — surface a clear response (e.g. 409 Conflict, or the existing review's status) when a request is rejected/deduplicated
- Possibly a migration if going the DB-constraint route (e.g. `alembic/versions/...` adding a unique partial index on `profile_id` for reviews in an "in-progress" state)
- Tests: new/updated test alongside existing `tests/` coverage for `review_service`

### Plan

1. **Choose the guard mechanism.** Decide between (a) an in-process per-profile asyncio lock/dict, (b) a DB-level advisory lock or unique constraint on "one in-progress review per profile_id", or (c) a simple "check for existing in-progress review, reject if found" read-then-write guard. (DB-level is safer across multiple worker processes; in-process lock is simpler but only works for a single-process deployment.)
2. **Implement the guard in `create_review()`.** Before calling `process_review()`, check/acquire the lock for `profile_id`. If unavailable, return early with a clear rejection (or return the existing in-flight review's identifier).
3. **Ensure the lock is always released.** Wrap `process_review()` in try/finally (or equivalent) so a crash mid-pipeline doesn't leave a profile permanently locked out of future reviews.
4. **Update `api/routes/reviews.py`** to handle the new rejection/duplicate case with an appropriate HTTP status and message instead of silently proceeding.
5. **Add regression tests** covering: (a) two concurrent requests for the same profile → only one ingestion/review happens, (b) two concurrent requests for *different* profiles → both proceed normally and independently, (c) a crashed/failed review releases the lock so a later request can proceed.

### Inputs & outputs

- **Input:** two (or more) near-simultaneous `POST /reviews` requests (or direct `create_review()` calls) with the same `profile_id`.
- **Output:** exactly one ingestion run and one `Review` record produced for that profile from the overlapping requests; the rejected/duplicate request gets a clear, documented response rather than silently racing.

### Risks & unknowns

- Whether the app runs as a single process or multiple worker processes/replicas — this determines whether an in-memory lock is sufficient or whether the guard must live in the DB.
- Whether `process_review()` can legitimately be re-triggered on purpose (e.g. "force re-review" from the UI) — the fix must not accidentally block a deliberate re-run.
- Lock cleanup on crash/timeout — need to confirm there's no scenario where a profile gets stuck "locked" forever.
- Whether other endpoints besides `POST /reviews` can also trigger `process_review()` for the same profile (need to check for other call sites).

### Edge cases

- Two requests for the same profile arriving genuinely simultaneously (race at the lock-acquisition step itself).
- A request for profile A and a request for profile B at the same time — must not block each other.
- The in-flight review fails/throws partway through — lock must still be released.
- A duplicate request arrives *just after* the first review finishes — should be allowed to start fresh, not be blocked by a stale lock.
- Server restart mid-review — any in-memory lock state would be lost; DB-level guard should recover cleanly on restart.
