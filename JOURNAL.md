## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/80

**Issue title:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
Deleting a profile is supposed to remove everything tied to it, but the vector-store embeddings created during ingestion are never cleaned up. Reviews and ingested-source database rows already cascade correctly in `core/services/profile_service.py`, but that function has no knowledge of the vector store, so each profile's embeddings — stored in a dedicated ChromaDB collection named `profile_{profile_id}` — are left orphaned after deletion. A `delete_by_source_id` method already exists on `VectorStore` (`rag/retriever/vector_store.py`) but is never called from anywhere. A successful fix adds a way to delete a profile's embedding collection and wires it into `delete_profile` so that removing a profile leaves no orphaned vector data behind.

**Branch name:** `fix/80-clean-up-orphaned-embeddings`

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger
