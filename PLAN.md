## Solution Plan

**Issue:** [DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings](https://github.com/ascherj/pathreview/issues/80)

## 1. Problem Overview (Understand)

- **Expected Behavior:** Sending a `DELETE /profiles/{profile_id}` request should remove the profile and all associated data including reviews, ingested sources, and ChromaDB vector embeddings.
- **Actual Behavior:** 
  - **Postgres (SQL):** The Postgres side is already handled correctly. `Review` and `IngestedSource` models have cascade settings, and `delete_profile()` in `core/services/profile_service.py` removes SQL records.
  - **ChromaDB (Vector Store):** Embeddings live outside Postgres in a Chroma collection named `profile_{profile_id}`. `delete_profile()` never calls ChromaDB, leaving orphaned embeddings permanently in the vector store after SQL rows are deleted.
- **Reproduction:** `tests/unit/test_profile_delete_cascade.py` seeds a test ChromaDB collection, runs `delete_profile()`, and fails because 1 embedding remains.

---

## 2. File & Component Map

| File Path | Role & Changes Needed |
| :--- | :--- |
| **`rag/retriever/vector_store.py`** | Add `delete_collection(collection_name: str)` method to safely drop a Chroma collection. |
| **`core/services/profile_service.py`** | Update `delete_profile()` to invoke ChromaDB collection cleanup during profile deletion. |
| **`rag/retriever/hybrid.py`** | Source of the `profile_{profile_id}` naming convention. Extract/share helper to avoid hardcoded duplicates. |
| **`api/routes/profiles.py`** | Verify `delete_profile_endpoint()` error handling behavior if vector cleanup fails. |
| **`tests/unit/test_profile_delete_cascade.py`** | Existing reproduction test. Update to confirm collection cleanup and handle missing collections. |

---

## 3. Implementation Plan

### Step 1: Add `delete_collection` to `VectorStore`
- Open `rag/retriever/vector_store.py`.
- Add `delete_collection(collection_name: str) -> None`.
- Wrap `self.client.delete_collection(name=collection_name)`.
- Catch exceptions (e.g., `ValueError` or collection not found) so profiles without ingested sources do not cause a crash.

### Step 2: Wire `VectorStore` into `profile_service.py`
- Import or construct `VectorStore` inside `core/services/profile_service.py` using standard configuration settings (`core/config.py`).
- Ensure no circular imports are introduced between service layers and retriever components.

### Step 3: Trigger Collection Cleanup in `delete_profile()`
- In `delete_profile()`, trigger `vector_store.delete_collection(f"profile_{profile_id}")`.
- **Execution Order:** Perform the vector store delete **before** committing the final SQL transaction. If ChromaDB fails, roll back SQL so database state remains consistent.

### Step 4: Update Unit Tests
- Run `pytest tests/unit/test_profile_delete_cascade.py` to confirm it passes (0 embeddings remaining).
- Add a test case for deleting a profile with 0 ingested sources to verify missing collections are handled gracefully.

### Step 5: Local Verification
1. Start services: `docker compose up -d`.
2. Run setup: `make setup`.
3. Create a profile and populate `profile_{id}` in ChromaDB — via the ingestion route if available, or by seeding directly with `VectorStore.add_chunks()` (same approach as the unit test) if not.
4. Send `DELETE /profiles/{id}`.
5. Inspect ChromaDB client to confirm `profile_{id}` collection no longer exists.

---

## 4. Inputs, Outputs & Edge Cases

- **Inputs:** `profile_id` (UUID), `user_id` (UUID).
- **Outputs:** `bool` status; removes SQL rows and deletes the `profile_{profile_id}` collection.

### Edge Cases to Handle:
1. **Missing Collection:** Profile has no ingested sources. `delete_collection` must catch non-existent collection errors and pass.
2. **Multiple Sources:** Single `delete_collection()` call clears all sources under that profile at once.
3. **Repeated Requests:** Duplicate `DELETE` calls hit `get_profile` returning `None` without attempting redundant Chroma calls.
4. **Service Unreachable:** If ChromaDB goes down, raise an error and abort SQL commit to prevent orphaned data.