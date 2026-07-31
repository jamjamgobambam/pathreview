## Solution plan

**Issue:** Vector store returns stale embeddings after a document is re-ingested —
https://github.com/jamjamgobambam/pathreview/issues/27

### Understand
When a profile's document (README, resume, or repo metadata) is edited and
re-ingested, the RAG vector store keeps the *previous* version's embeddings
alongside the new ones. Retrieval can then surface outdated chunks and feed them
into the generated review.

Root cause: the ingestion path appends and never cleans up.
`BatchEmbeddingProcessor._store_embedding()` writes with a raw
`vector_db.add(ids=[f"{source_id}_chunk_{i}"], ...)` and no delete.
`VectorStore.delete_by_source_id()` exists to purge a source's vectors but is
never called anywhere. And `source_id` embeds a content hash
(`IngestionPipeline._hash_content`), so an edited document gets a brand-new
`source_id` and new vector ids — the old vectors can't be matched by the new id
and are orphaned in the collection.

- Expected: after re-ingesting an edited document, the store holds exactly one
  current set of chunks for that logical source.
- Actual: the store holds both the old and new versions' chunks. Confirmed locally
  by `tests/unit/test_reingest_stale_embeddings.py` — after two `ingest_readme`
  calls (original + edited) the store contains two `source_id`s instead of one.

### Map
- `ingestion/pipeline.py` — `ingest_resume` / `ingest_readme` / `ingest_repo_metadata`
  compute `source_id` (with content hash) and call `batch_processor.process(chunks)`.
  This is where a stable "logical source" key must be derived and cleanup triggered.
- `ingestion/embeddings/batch_processor.py` — `_store_embedding()` builds the vector
  id and calls `vector_db.add(...)`. Must write a stable key into stored metadata.
- `rag/retriever/vector_store.py` — `delete_by_source_id()` (currently dead code) is
  the deletion primitive to reuse/repair; note it filters `metadata.source_id`.
- `core/services/review_service.py` — `_run_ingestion_pipeline` constructs the
  pipeline and decides what `vector_db` actually is (raw Chroma collection vs the
  `VectorStore` wrapper). Must confirm which, since deletion lives on the wrapper.
- Tests: `tests/unit/test_batch_processor.py` (mock `vector_db` pattern to reuse) and
  the new `tests/unit/test_reingest_stale_embeddings.py` (the reproduction).

### Plan
1. Derive a **stable logical-source id** in `IngestionPipeline` (e.g.
   `readme_{profile_id}_{repo_name}`, `resume_{profile_id}`,
   `repo_{profile_id}_{repo_name}`) without the content hash, and add it to each
   chunk's metadata as `base_source_id`.
2. In `_store_embedding`, persist `base_source_id` in the stored metadata so it is
   filterable in the collection.
3. Add a **delete-before-store** step: before `batch_processor.process(chunks)`,
   purge existing vectors for that `base_source_id` (Chroma
   `collection.delete(where=...)`, reusing/repairing `VectorStore.delete_by_source_id`
   to filter on the stable key). Make it a safe no-op when nothing matches.
4. Reconcile the `vector_db` object: ensure the component that deletes has a
   `delete(where=...)`-capable handle (either call the collection directly or pass the
   `VectorStore` wrapper through `review_service._run_ingestion_pipeline`).
5. Remove the `xfail` marker from `tests/unit/test_reingest_stale_embeddings.py` and
   add cases for the edge cases below; confirm `make test-unit` and `make check` pass.

### Inputs & outputs
- Input: chunks whose metadata carries `profile_id`, `source_type`, `repo_name` (for
  readme/repo), the content-hash `source_id`, and the new `base_source_id`.
- Output / behavior change: after ingest, the store contains only the current
  version's chunks for a given `base_source_id`. New behavior: a delete-before-store
  call in the pipeline and a `base_source_id` field in stored metadata. No change to
  `VectorStore.query()` or any retrieval/API signature — retrieval simply stops
  seeing stale chunks.

### Risks & unknowns
- **Legacy data**: vectors written before the fix won't have `base_source_id`, so a
  `where={"base_source_id": ...}` delete won't catch them. Tied to
  `batch_processor._store_embedding` + `vector_store.delete_by_source_id`: also delete
  by a legacy id/prefix pattern, or accept that only post-fix data is cleaned.
- **What `vector_db` really is**: `IngestionPipeline.__init__` takes a raw `vector_db`,
  but `delete_by_source_id` is a `VectorStore` method — confirm in
  `core/services/review_service.py:_run_ingestion_pipeline` whether a collection or a
  wrapper is passed, else the delete call has no home.
- **Chroma delete semantics**: `collection.delete(where=...)` requires a non-empty,
  supported filter; verify against the pinned Chroma version.
- `_check_skip` (`pipeline.py:280`) is a placeholder; confirm it doesn't short-circuit
  re-ingestion of edited content (different `source_id` → won't skip, so OK).

### Edge cases
1. Re-ingesting an **edited** document (new content hash) — old vectors purged (primary).
2. Re-ingesting an **identical** document (same hash/ids) — no duplicates and no error
   (raw `.add` on duplicate ids can raise in ChromaDB; delete-before-store or upsert
   must handle it).
3. **First-time** ingestion (no prior vectors) — delete-before-store is a safe no-op.
4. **Two repos, one profile** — deleting repoX's README vectors must not touch repoY's
   (`base_source_id` must include `repo_name`).
5. **Multi-chunk** document — all old chunks (`chunk_0..N`) removed, not just `chunk_0`.
