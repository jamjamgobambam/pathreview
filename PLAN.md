## Solution plan

**Issue:** Stale embeddings remain after README re-ingestion — [#27](https://github.com/ascherj/pathreview/issues/27)

### Understand
When a README is updated and re-ingested, the old embeddings stay in the vector
store next to the new ones, so the retriever can return chunks that no longer
reflect the current document.

Two things combine to cause this:

1. **Content-hash source ids.** `IngestionPipeline.ingest_readme`
   ([ingestion/pipeline.py:143](ingestion/pipeline.py#L143)) builds
   `source_id = f"readme_{profile_id}_{repo_name}_{self._hash_content(content)}"`.
   Because the content hash is part of the id, an edited README gets a *new*
   source_id and its chunks are written under new ids instead of replacing the
   old ones. The embedding id itself is `f"{source_id}_chunk_{chunk_index}"`
   ([ingestion/embeddings/batch_processor.py:108](ingestion/embeddings/batch_processor.py#L108)),
   so the ids never collide across versions.
2. **Cleanup is never invoked.** `VectorStore.delete_by_source_id`
   ([rag/retriever/vector_store.py:115](rag/retriever/vector_store.py#L115))
   exists but has no callers (confirmed by grep). Nothing evicts the previous
   version's chunks.

- **Expected:** after re-ingesting an updated README, the store holds only the
  current document's chunks; a query never returns pre-update content.
- **Actual:** both old and new chunks are present; a query can return stale text
  (reproduced in [tests/integration/test_stale_embeddings_repro.py](tests/integration/test_stale_embeddings_repro.py)).

### Map
Files I expect to touch:

- [ingestion/pipeline.py](ingestion/pipeline.py) — `ingest_readme` (and the same
  pattern in `ingest_resume` / `ingest_repo_metadata`): introduce a stable
  document id and call cleanup before storing new chunks.
- [rag/retriever/vector_store.py](rag/retriever/vector_store.py) —
  `delete_by_source_id`: make it delete by the stable document key; confirm it
  is safe when the collection is empty / key absent.
- [ingestion/embeddings/batch_processor.py](ingestion/embeddings/batch_processor.py)
  — reconcile the id/metadata scheme so the value used for deletion matches the
  value stored at write time.
- [tests/integration/test_stale_embeddings_repro.py](tests/integration/test_stale_embeddings_repro.py)
  — invert the `BUG` assertion into a regression test once the fix lands.

### Plan
1. **Introduce a stable document key.** Split the current `source_id` into a
   stable `document_id` (`readme_{profile_id}_{repo_name}`, no content hash) plus
   a separate `content_hash` used only for the skip/dedup check. Store the
   `document_id` in each chunk's metadata so it can be targeted for deletion.
2. **Delete-before-insert on re-ingestion.** In `ingest_readme`, call
   `VectorStore.delete_by_source_id(document_id, collection)` (renamed/adjusted to
   filter on `document_id`) *before* `batch_processor.process(chunks)`, so the old
   version is cleared first.
3. **Align the vector-store and batch-processor id scheme.** Ensure the metadata
   key written by `_store_embedding` is the same key `delete_by_source_id`
   filters on (today one writes raw `chunk.metadata`, the wrapper writes a
   `source_id` field) so deletion actually matches stored rows.
4. **Convert the reproduction into a regression test.** Flip the assertion in
   `test_stale_embeddings_repro.py` to assert only the current chunk survives,
   and add a case where an unchanged README re-ingest is still skipped.
5. **Run the suite** (`make test` / `pytest tests/`) to confirm no regressions in
   ingestion or retrieval.

### Inputs & outputs
- **Inputs:** `ingest_readme(profile_id, repo_name, content)` — unchanged public
  signature. Internally it now derives a stable `document_id` and a
  `content_hash`.
- **Outputs / behavior changes:**
  - `delete_by_source_id` is invoked with the stable `document_id` on every
    re-ingestion, removing prior chunks before new ones are written.
  - Chunk metadata gains/normalizes a `document_id` field.
  - Net effect: the collection contains exactly one set of chunks per
    `(profile_id, repo_name)` README, always reflecting the latest content.

### Risks & unknowns
- **Two divergent write paths.** `batch_processor._store_embedding` calls
  `vector_db.add(...)` directly, while `VectorStore.add_chunks` reads
  `chunk.id`/`chunk.source_id` — but `Chunk` ([ingestion/chunking/base.py](ingestion/chunking/base.py))
  only has `text` and `metadata`. I need to confirm which path production uses
  before changing the id scheme, or the delete filter won't match the stored key.
- **Metadata-filter correctness in ChromaDB.** `delete_by_source_id` uses
  `where={"source_id": {"$eq": ...}}`; I need to verify the field name and that
  deleting on an empty/missing key is a no-op rather than an error.
- **Skip logic coupling.** `_check_skip` ([ingestion/pipeline.py:280](ingestion/pipeline.py#L280))
  keys on `source_id`; if I stabilize the id I must move the "already ingested"
  check onto `content_hash` or unchanged READMEs will be needlessly re-embedded.
- **`_record_ingested_source` is a placeholder** (no real DB write), so I can't
  rely on it to detect prior versions — the vector store is the source of truth.

### Edge cases
- **First-time ingestion** (no prior chunks): delete-before-insert must be a safe
  no-op when `document_id` matches nothing.
- **Unchanged README re-ingested:** should still be skipped (same `content_hash`),
  not deleted-and-reinserted.
- **README shrinks** (v2 has fewer chunks than v1): leftover high-index chunks
  from v1 must be removed, not just overwritten index-by-index.
- **Same repo name across two different profiles:** deleting `document_id` for
  profile A must not touch profile B's chunks (id includes `profile_id`).
- **Empty / whitespace-only README:** ingestion should not crash and should leave
  no stale chunks behind.
