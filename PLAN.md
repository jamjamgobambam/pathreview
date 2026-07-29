# PLAN

## Solution plan

**Issue:** [#82 — Concurrent review requests for the same profile can produce inconsistent results](https://github.com/ascherj/pathreview/issues/82)

### Understand

`process_review` in `core/services/review_service.py` has no synchronization on `profile_id`. When `POST /reviews` is called twice for the same profile close together, `create_review_endpoint` in `api/routes/reviews.py` schedules two independent `process_review` background tasks via `BackgroundTasks.add_task`, and nothing prevents them from running fully concurrently against the same profile.

I confirmed this concretely with a failing integration test (`tests/integration/test_review_service.py`): two `process_review` calls for the same profile both start before either finishes, with the second run beginning while the first is still mid-pipeline.

- **Expected:** a second review request for a profile that already has a review in flight waits for the first to finish before it starts processing — reviews for the same profile are serialized.
- **Actual:** both requests run the full ingestion → agent → RAG → safety pipeline in parallel with no coordination, so the second loop can act on profile-related state the first is still in the middle of changing, producing inconsistent results between the two reviews.

### Map

- `core/services/review_service.py` — `process_review` is where the lock needs to be acquired and held around the ingestion/agent/RAG/safety pipeline. This is the primary file to change.
- `api/routes/reviews.py` — `create_review_endpoint` schedules the background task; not expected to change, but relevant to understand the call flow (each request gets its own `process_review` invocation with its own DB session).
- `core/database.py` — `AsyncSessionLocal`/engine; acquiring a Postgres advisory lock means running a raw SQL statement through the existing async session, so worth confirming there's no existing helper for raw SQL execution before adding one.
- `tests/integration/test_review_service.py` — the reproduction test. The fix's job is to flip this from failing to passing without modifying the test itself.
- `tests/unit/test_review_service.py` — existing unit tests for `create_review`/`get_review`/`list_reviews`; will likely need a new unit test for whatever helper computes the lock key.

### Plan

1. Add a helper that deterministically converts a profile UUID into the 64-bit integer key `pg_advisory_lock`/`pg_advisory_xact_lock` require (they take `bigint`, not a UUID string), e.g. via Postgres's own `hashtext()` run as part of the lock-acquisition query.
2. In `process_review`, acquire the advisory lock before Step 1 (setting status to `"processing"`) using the same session/connection that will be used for the rest of the pipeline.
3. **Resolved:** use `pg_advisory_xact_lock` (transaction-scoped), acquired *after* the existing "processing" status commit, not a session-scoped `pg_advisory_lock`/`pg_advisory_unlock` pair. Session-scoped locks are tied to the physical DB connection, not the transaction -- and `AsyncSession` doesn't guarantee the same connection stays checked out across multiple commits, especially under concurrent load. Getting that wrong would mean the lock silently protects nothing exactly when concurrency is high, which defeats the point. The only structural change needed is removing the one `await db.commit()` inside `_run_ingestion_pipeline`, so the transaction opened after the "processing" commit stays open until the single terminal commit (success or safety-failure branch) -- no restructuring of the status-commit flow itself, and the "processing" status stays immediately visible to pollers exactly as it is today.
4. Confirm `tests/integration/test_review_service.py` flips from failing to passing with no changes to the test itself — that's the acceptance signal for the fix.
5. Add a second integration test proving the lock is scoped *per profile*, not global: two concurrent reviews for two *different* profiles should still run fully in parallel, unaffected by each other.

### Inputs & outputs

- **Input:** `profile_id` (UUID), already passed into `process_review` — no new inputs needed.
- **Output/change:** `process_review` changes from "runs immediately and unconditionally" to "blocks until any other in-flight review for the same `profile_id` completes, then proceeds." No API contract change — `POST /reviews` still returns immediately with `status="pending"`; the change is entirely in how the background task serializes internally.

### Risks & unknowns

- **Multi-commit structure conflicts with transaction-scoped locks.** As noted above, `process_review`'s several intermediate `db.commit()` calls mean a naive `pg_advisory_xact_lock` releases too early. This is the biggest open design question and needs to be resolved before the lock actually does anything.
- **Background tasks use their own session per call** (confirmed during reproduction: each `process_review` invocation gets a fresh `AsyncSessionLocal()`), so the lock has to be acquired inside `process_review` itself — it can't be handled at the FastAPI dependency/route layer.
- **Lock release on failure.** `process_review` already has a `except Exception` block that marks the review `"failed"`. Whatever locking mechanism I use has to release the lock on that path too, or a single failed review would permanently block all future reviews for that profile.
- **Advisory lock key collisions.** Hashing a UUID down to a 64-bit int for the lock key means two different `profile_id`s could theoretically collide and serialize against each other unnecessarily. Low risk in practice, but worth a code comment.
- **Two unrelated pre-existing bugs surfaced during reproduction, discovered while building the repro test:** `_run_ingestion_pipeline` passes a `raw_data` kwarg that doesn't exist on the `IngestedSource` model (silently swallowed by a blanket `except`, so ingestion never actually writes rows today), and `core/services/review_service.py` currently fails `mypy` on `main` independent of anything here. Neither blocks implementing the lock, but the ingestion bug means `IngestedSource` row counts can't be used as a secondary signal that the fix is working.
- **No timeout on held locks.** If a review genuinely hangs, the lock blocks all subsequent reviews for that profile indefinitely. Postgres releases a transaction-scoped advisory lock automatically on commit, rollback, or a lost connection, which covers crashes, but not a review that's simply slow. Deciding whether that needs a safeguard, or is out of scope for this issue.

### Edge cases

- Two reviews submitted for the **same** profile concurrently → second one waits, then runs after the first completes (the core fix; this is what the reproduction test checks).
- Two reviews submitted for **different** profiles concurrently → both proceed fully in parallel, unaffected by each other's locks (needs its own test, per Plan step 5).
- A review that **fails partway through** (exception, or safety check failure) → the lock must still release so the next review for that profile isn't permanently blocked.
- **Rapid sequential** requests (not truly concurrent, but request N+1 arrives just as request N's review finishes) → should acquire cleanly once released, no deadlock or double-lock.
- **Server crash while a review is mid-processing and holding the lock** → Postgres auto-releases transaction-scoped advisory locks when the owning connection closes or the transaction aborts, so a crash doesn't leave the profile permanently locked.
