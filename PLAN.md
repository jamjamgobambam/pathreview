## Solution plan

**Issue:** [#80 — DELETE /profiles/{profile_id} doesn't cascade to delete associated reviews and embeddings](https://github.com/ascherj/pathreview/issues/80)

### Understand

**Expected:** Deleting a profile should clean up everything tied to it — the reviews, the ingested sources, and the profile's embeddings — so nothing gets left behind pointing at a profile that no longer exists.

**Actual:** `delete_profile()` deletes the Postgres rows and even logs `profile_deleted_cascade`, so it *thinks* it did a full cleanup. But the profile's embeddings live in a separate ChromaDB collection that never gets touched, so every deleted profile leaks a whole collection of vectors.

**Root cause:** The delete path has no idea the vector store exists. `delete_profile()` in `core/services/profile_service.py` only talks to the SQL session. Each profile's vectors are stored in their own ChromaDB collection named `profile_{profile_id}` (that name is built in `rag/retriever/hybrid.py` line 42, and collections are created/written in `rag/retriever/vector_store.py`). Nothing in the delete flow ever removes that collection.

One thing worth calling out: the `Review` and `IngestedSource` rows are *already* cleaned up — `delete_profile()` deletes them explicitly, and the models also have `ondelete="CASCADE"` on their foreign keys. So despite the issue title saying "reviews and embeddings," the reviews half is effectively handled. The real, live gap is the embeddings.

### Map

Files I expect to touch or lean on:

- `core/services/profile_service.py` — `delete_profile()`. This is where the fix goes: after the DB rows are gone, drop the profile's ChromaDB collection.
- `rag/retriever/vector_store.py` — the `VectorStore` class. It has `delete_by_source_id()` but no way to drop a whole collection. I'll add a `delete_collection(name)` that wraps `self.client.delete_collection(name=...)`.
- `rag/retriever/hybrid.py` (line 42) — the canonical `f"profile_{profile_id}"` collection name. I want the delete path to reuse this, not hardcode a second copy that can drift.
- `core/config.py` — `vector_db_url`. I need to instantiate the vector store the same way the rest of the app does so I clean up the store ingestion actually writes to (see risks — there's a mismatch here).
- `api/routes/profiles.py` — `delete_profile_endpoint`. Probably unchanged, but I need to confirm it still returns 204 / 404 / 500 correctly once the service does more work.
- `tests/unit/test_profile_cascade_delete.py` — the reproduction test (already added this week). It should flip from red to green once the fix lands.

### Plan

1. Add `VectorStore.delete_collection(name)` in `rag/retriever/vector_store.py` that calls `self.client.delete_collection(name=name)` and treats "collection doesn't exist" as a no-op, so it's idempotent.
2. Pull the collection name into one shared helper (something like `collection_name_for_profile(profile_id) -> f"profile_{profile_id}"`) so the delete path and `hybrid.py` agree instead of hardcoding the format twice.
3. In `delete_profile()`, after the SQL rows are deleted, get a `VectorStore` handle and call `delete_collection(collection_name_for_profile(profile_id))`. Decide ordering relative to the SQL commit (see risks).
4. Wrap the vector-store cleanup so a Chroma failure doesn't blow up a delete that already succeeded in Postgres — log it loudly and follow whatever failure policy I settle on.
5. Point the reproduction test at the same store the fix uses (inject the client / monkeypatch the persist dir), confirm it goes green, and add a second test for the "profile had no embeddings" no-op case.

### Inputs & outputs

**Input:** `profile_id`, `user_id` (for the ownership check), the DB session, and a handle to the ChromaDB client / `VectorStore`.

**Output / change:** the profile plus its reviews and ingested sources are removed from Postgres (already happening today) **and** the `profile_{profile_id}` ChromaDB collection is removed. The endpoint still returns `204` on success and `404` when the profile isn't found or isn't owned by the caller. Net result: no orphaned vectors left behind.

### Risks & unknowns

- **Two systems, one delete.** Postgres and ChromaDB don't share a transaction. If the SQL commit succeeds but the Chroma delete fails (or the reverse), I get a half-deleted profile. I'm leaning toward: delete the SQL rows and commit first, then delete the Chroma collection, and if Chroma fails, log loudly rather than 500-ing a delete that already cleared the rows. Open question for Slack / office hours: does the cohort want strict all-or-nothing here?
- **Which Chroma client is real?** `core/config.py` sets `vector_db_url=http://localhost:8001` (an HTTP server), but `VectorStore.__init__` uses `chromadb.PersistentClient(path=".chromadb")` (a local dir). Those disagree. I need to confirm how the running app actually talks to Chroma before I hardcode a path, or I'll end up cleaning a different store than the one ingestion writes to.
- **Dependency injection.** `delete_profile()` is a plain function with no vector-store parameter. Adding one ripples out to the route in `api/routes/profiles.py` and any test that calls it. I want to keep the signature change small and backwards-safe.
- **Placeholder ingestion.** `review_service._run_ingestion_pipeline` and `_run_rag_retrieval_generation` are stubs right now and never actually call `add_chunks`, so I can't fully exercise this end-to-end through the UI. The failing unit test is my reliable proof until those paths are real.

### Edge cases

- Profile has no embeddings yet (collection was never created) → delete should be a clean no-op, not an error.
- Profile doesn't exist or isn't owned by the caller → still `404`, and don't touch Chroma at all.
- Delete called twice / profile already gone → idempotent, no crash.
- Chroma server unreachable at delete time → defined behavior (log + my chosen failure policy), never a silent `500` that leaves rows orphaned.
- Two profiles exist, only one is deleted → the other profile's collection is left completely untouched.
