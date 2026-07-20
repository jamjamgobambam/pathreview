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

**Reproduction commit link:** [to be filled in after pushing — commit SHA below]

**Reproduction summary:**
Added a failing unit test (`tests/unit/test_profile_service.py::TestDeleteProfileCascade::test_delete_profile_cleans_up_vector_store_collection`) that calls `delete_profile` with a mocked DB session and asserts `VectorStore().delete_collection(f"profile_{profile_id}")` is invoked. The test fails with `AssertionError: Expected 'delete_collection' to be called once. Called 0 times.`, confirming the vector-store cleanup is entirely absent from `delete_profile`.

**PLAN.md link:** [to be filled in after pushing — e.g. https://github.com/\<username\>/pathreview/blob/fix/80-clean-up-orphaned-embeddings/PLAN.md]

**Walkthrough video (recommended):** [pending]

**Blockers or open questions:**
`VectorStore` currently opens a local `.chromadb` directory via `PersistentClient`, while the deployed app uses a ChromaDB HTTP server configured via `vector_db_url`. The fix will use `VectorStore` as-is (consistent with the rest of the retrieval layer), but the underlying wiring mismatch means the cleanup call won't reach the production Chroma server until that separate issue is also addressed.
