## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/80

**Issue title:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Deleting a profile is supposed to remove everything tied to it, but the vector-store embeddings created during ingestion are never cleaned up. Reviews and ingested-source database rows already cascade correctly in `core/services/profile_service.py`, but that function has no knowledge of the vector store, so each profile's embeddings — stored in a dedicated ChromaDB collection named `profile_{profile_id}` — are left orphaned after deletion. A `delete_by_source_id` method already exists on `VectorStore` (`rag/retriever/vector_store.py`) but is never called from anywhere. A successful fix adds a way to delete a profile's embedding collection and wires it into `delete_profile` so that removing a profile leaves no orphaned vector data behind.

**Branch name:** `fix/80-clean-up-orphaned-embeddings`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jon-tous/pathreview/commit/ee2070d4392a976ade239a664e1808ad1ff66369

**Reproduction summary:**
Added a failing unit test (`tests/unit/test_profile_service.py::TestDeleteProfileCascade::test_delete_profile_cleans_up_vector_store_collection`) that calls `delete_profile` with a mocked DB session and asserts `VectorStore().delete_collection(f"profile_{profile_id}")` is invoked. The test fails with `AssertionError: Expected 'delete_collection' to be called once. Called 0 times.`, confirming the vector-store cleanup is entirely absent from `delete_profile`.

**PLAN.md link:** https://github.com/jon-tous/pathreview/blob/fix/80-clean-up-orphaned-embeddings/PLAN.md

**Blockers or open questions:**
`VectorStore` currently opens a local `.chromadb` directory via `PersistentClient`, while the deployed app uses a ChromaDB HTTP server configured via `vector_db_url`. The fix will use `VectorStore` as-is (consistent with the rest of the retrieval layer), but the underlying wiring mismatch means the cleanup call won't reach the production Chroma server until that separate issue is also addressed.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All three sub-tasks from PLAN.md are complete. Added `delete_collection(name)` to `VectorStore` (`rag/retriever/vector_store.py`), wired it into `delete_profile` (`core/services/profile_service.py`) as a best-effort call after the DB commit, and updated the test suite. The formerly failing reproduction test now passes alongside three additional tests: one verifying the correct collection name is used, one confirming the delete still returns `True` when the vector-store cleanup raises, and two new unit tests for `VectorStore.delete_collection` itself (collection exists and collection missing cases).

**Next steps:**
Open a draft PR, fill in the PR template, and collect peer or mentor feedback before marking it ready for review. Will also write the Check-in 2 entry once the PR is submitted.

**Blockers:**
None. `make test-unit` went from 54 → 53 failures (our reproduction test now passes); `make check` went from 181 → 178 lint errors (ruff auto-removed three pre-existing unused imports during staging). Neither change introduced new failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/298

**Branch:** `fix/80-clean-up-orphaned-embeddings`

**What you built:**
Added `VectorStore.delete_collection` and wired it into `delete_profile` so that deleting a profile now also removes the associated ChromaDB collection (`profile_{profile_id}`), preventing orphaned embeddings. The cleanup is best-effort — errors are logged but don't surface to the caller, since the DB delete (the primary operation) has already committed successfully.

**Tests added or updated:**
- `tests/unit/test_profile_service.py` — updated to patch `VectorStore` at the correct import path; added tests for the cleanup call and the best-effort error-suppression behaviour
- `tests/unit/test_vector_store.py` — new file; covers `delete_collection` when the collection exists and when it doesn't (no-op on `ValueError`)

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none
