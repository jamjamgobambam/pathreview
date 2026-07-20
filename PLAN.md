## Solution plan

**Issue:** `DELETE /profiles/{profile_id}` doesn't cascade to delete associated reviews and embeddings — https://github.com/jamjamgobambam/pathreview/issues/80

### Understand

**Root cause:** `delete_profile` in `core/services/profile_service.py` has no knowledge of the vector store. It correctly cascades SQL-level deletions (Reviews, IngestedSources, and the Profile row itself), but it never touches ChromaDB. Each profile's embeddings live in a dedicated ChromaDB collection named `profile_{profile_id}` — a convention established in `rag/retriever/hybrid.py:42`. Nothing ever removes that collection when a profile is deleted.

**Expected behavior:** All data tied to a profile is removed on deletion, including the ChromaDB collection holding its embeddings.

**Actual behavior:** The ChromaDB collection `profile_{profile_id}` persists in the vector store indefinitely after the database rows are gone, occupying storage and potentially polluting future retrieval results if a new profile is later assigned the same ID.

A `delete_by_source_id` method already exists on `VectorStore` (`rag/retriever/vector_store.py:115`) and was intended for cleanup, but is never called from anywhere. The IngestedSource database model also doesn't store the string `source_id` format used as chunk metadata in ChromaDB (e.g., `resume_{profile_id}_{hash}`), so per-source deletion isn't feasible from DB records anyway. The cleanest fix is to delete the entire `profile_{profile_id}` collection at once.

### Map

Files this fix touches:

| File | Change |
|---|---|
| `rag/retriever/vector_store.py` | Add `delete_collection(name)` method |
| `core/services/profile_service.py` | Import `VectorStore`; call `delete_collection` inside `delete_profile` |
| `tests/unit/test_profile_service.py` | Update failing reproduction test to pass; add edge-case coverage |
| `tests/unit/test_vector_store.py` | New file — unit tests for `delete_collection` |

Files consulted but not changed:

- `rag/retriever/hybrid.py:42` — establishes the `profile_{profile_id}` collection naming convention
- `core/models/ingested_source.py` — confirms no `source_id` string field (rules out per-source loop approach)
- `ingestion/pipeline.py` — confirms `_record_ingested_source` is a stub; source IDs aren't persisted to DB
- `api/routes/profiles.py:196-220` — DELETE endpoint that calls `delete_profile`

### Plan

1. **Add `VectorStore.delete_collection`** (`rag/retriever/vector_store.py`)
   - New method: `def delete_collection(self, name: str) -> None`
   - Calls `self.client.delete_collection(name=name)`
   - Wraps in try/except: `ValueError` when collection doesn't exist → log a warning and return (no-op); other exceptions → re-raise

2. **Wire cleanup into `delete_profile`** (`core/services/profile_service.py`)
   - Add import: `from rag.retriever.vector_store import VectorStore`
   - Inside `delete_profile`, after the DB deletes and commit, instantiate `VectorStore()` and call `vector_store.delete_collection(f"profile_{profile_id}")`
   - Keep it inside the existing `try/except` block so failures are logged consistently

3. **Update the reproduction test** (`tests/unit/test_profile_service.py`)
   - Change the patch path from `rag.retriever.vector_store.VectorStore` to `core.services.profile_service.VectorStore` (where it will be imported after the fix)
   - The test should now pass, confirming the fix works
   - Add a test for the case where vector store deletion raises (e.g., collection doesn't exist) to ensure `delete_profile` handles it gracefully

4. **Add `VectorStore.delete_collection` unit tests** (`tests/unit/test_vector_store.py`)
   - Mock `chromadb.PersistentClient` to avoid real disk I/O
   - Test: collection exists → `client.delete_collection` called with correct name
   - Test: collection doesn't exist (ValueError) → no exception raised, warning logged

### Inputs & outputs

**Input:** `delete_profile(db, profile_id, user_id)` — unchanged signature.

**Output changes:**
- ChromaDB collection `profile_{profile_id}` is deleted (or confirmed absent) in addition to the existing SQL cascade
- Return value (`True`/`False`) and exception behavior are unchanged from the caller's perspective
- A log line is emitted for the vector-store cleanup attempt (consistent with the existing `profile_deleted_cascade` log)

### Risks & unknowns

- **VectorStore uses `PersistentClient`, not `HttpClient`:** `VectorStore.__init__` always opens a local `.chromadb` directory, but `core/config.py` and `docker-compose.yml` define a Chroma HTTP server on port 8001. This pre-existing disconnect means production ingestion data lives on the HTTP server, while `VectorStore()` opens a local dir. The fix is still correct in principle — the cleanup call goes to wherever `VectorStore` is currently pointed. Properly wiring `VectorStore` to `vector_db_url` is a separate issue and out of scope here.

- **Delete ordering:** If vector-store cleanup succeeds but the subsequent DB commit fails (or vice versa), the two stores end up inconsistent. Deleting vector data *after* the DB commit means: if DB commit fails, vector data was already rolled back but vector embeddings may be gone. For this fix we'll delete the ChromaDB collection after a successful DB commit to prefer leaving orphaned vector data over losing data that should still be accessible.

### Edge cases

- **Profile was never ingested** (no ChromaDB collection exists): `delete_collection` catches the `ValueError` from `client.delete_collection` and logs a warning — no error propagated to the caller.
- **ChromaDB unavailable:** Exception propagates up; the caller receives a 500. This is acceptable — the same behavior as if the DB were unavailable.
- **Collection exists but is empty:** No special handling needed; `client.delete_collection` handles empty collections identically to non-empty ones.
