## Solution plan

**Issue:** DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings — https://github.com/ascherj/pathreview/issues/80

### Understand
The issue as filed is partly stale: `delete_profile()` in `core/services/profile_service.py` already deletes the profile's `Review` and `IngestedSource` rows inside a transaction, and `core/models/profile.py` already configures both ORM `cascade="all, delete-orphan"` and FK `ondelete="CASCADE"` for those relationships — so the Postgres-cascade part of the bug report doesn't reproduce. The real, still-open gap is the vector store: reviews get embedded into a Chroma collection named `profile_{profile_id}` (see `rag/retriever/hybrid.py`), managed by `VectorStore` (`rag/retriever/vector_store.py`), and `delete_profile()` never calls into it. Expected behavior: deleting a profile removes every trace of it, including its embeddings. Actual behavior: only the Postgres rows are removed; the Chroma collection and its embeddings persist indefinitely with no code path to clean them up.

### Map
- `core/services/profile_service.py` — `delete_profile()`, the function that needs to change
- `rag/retriever/vector_store.py` — `VectorStore`; has `delete_by_source_id()` but no method to delete/clear a whole collection
- `rag/retriever/hybrid.py` (line 42) — defines the `profile_{profile_id}` collection-naming convention that the fix must reuse exactly
- `api/routes/profiles.py` — `delete_profile_endpoint()`, the call site that will need a `VectorStore` instance wired in
- `tests/unit/test_profile_service_vector_cleanup.py` — this week's reproduction test; will be extended into the regression test for the fix

### Plan
1. Add a `delete_collection(name: str) -> None` method to `VectorStore` (`rag/retriever/vector_store.py`) that calls `self.client.delete_collection(name=name)` and tolerates the collection not existing.
2. Thread a `VectorStore` instance into `delete_profile()` (new parameter) and call `vector_store.delete_collection(f"profile_{profile_id}")` as part of the deletion flow.
3. Delete the vector collection only *after* the DB commit succeeds, and log-but-don't-fail the request if vector cleanup errors — Chroma isn't part of the SQL transaction, so there's no atomicity between the two stores.
4. Wire the `VectorStore` dependency through `api/routes/profiles.py`'s `delete_profile_endpoint()` call site (constructor arg or FastAPI `Depends()`).
5. Extend `tests/unit/test_profile_service_vector_cleanup.py` to assert the Chroma collection is gone after `delete_profile()` succeeds, flipping this week's "documents the bug" assertion into a real regression test.

### Inputs & outputs
`delete_profile()` gains one new input: a `VectorStore` instance (alongside the existing `db`, `profile_id`, `user_id`). Its return value is unchanged (`bool`, `True`/`False` for found/not-found). The new output is a side effect: the `profile_{profile_id}` Chroma collection is deleted, so no embeddings remain queryable for that profile after a successful call.

### Risks & unknowns
- `VectorStore` and `IngestionPipeline` (`ingestion/pipeline.py`) are not instantiated anywhere in the current app — `grep -rn "VectorStore(\|IngestionPipeline("` across the repo returns zero call sites, and the real review-generation path (`core/services/review_service.py:_run_rag_retrieval_generation`) is fully placeholder code. So today nothing actually populates the `profile_{profile_id}` collection in production — this bug is real but currently latent. The fix still needs to land now since it's the issue as filed, but there's no way to verify it against the live running app yet, only via a directly-seeded vector store (as this week's test does).
- No `VectorStore` dependency-injection pattern exists yet in `api/routes/profiles.py` — need to pick module-level singleton vs. FastAPI `Depends()`, and that choice could diverge from how other services get wired up later.
- Chroma collection deletion is not part of the SQL transaction — a crash between the DB commit and the vector cleanup call leaves an orphaned collection with no retry path today.
- Two adjacent, pre-existing bugs are unrelated to this issue but easy to confuse with it: `ingestion/pipeline.py`'s `_check_skip` (~line 289) queries `self.db_session.query("IngestedSource")` with a literal string instead of the ORM model, and `core/services/review_service.py`'s `_run_ingestion_pipeline` (lines 216/241/265) constructs `IngestedSource(..., raw_data=...)` even though the model has no `raw_data` column, which would raise `TypeError` if that path ever ran against a populated profile. Neither should be fixed as part of #80.

### Edge cases
- A profile with no `IngestedSource` rows at all (nothing was ever ingested, so no Chroma collection was ever created) — `delete_collection()` must not raise in this case.
- A profile deletion retried after a partial prior failure (DB commit succeeded, vector cleanup failed) — the second `delete_profile()` call will 404 (profile already gone) before it ever reaches vector cleanup, so the orphaned collection stays orphaned; needs to be an accepted limitation or handled with a defensive "delete the collection even if the profile row is already gone" fallback.
