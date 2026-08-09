# Solution plan

**Issue:** Vector store returns stale embeddings after a document is re-ingested — [#27](https://github.com/ascherj/pathreview/issues/27)

### Understand

The root cause is how `source_id` is defined during ingestion. Today it is:

```
source_id = f"readme_{profile_id}_{repo_name}_{hash(content)}"
```

The content hash is baked into the identity of the source. That id is used to
decide whether a document has already been ingested (the skip check) and to key
every chunk stored in the vector DB.

Because the hash changes whenever the README text changes, the **same** README
with edited content is treated as a **brand new** source: it gets a new
`source_id`, the skip check never matches, and its chunks are written alongside
the old version's chunks. Nothing ever deletes the previous version.

- **Expected:** after re-ingesting an edited README, only the current version's
  chunks are retrievable.
- **Actual:** old and new chunks coexist under different hashed ids, so the
  retriever can surface stale, outdated content.

Confirmed by the reproduction test `tests/unit/test_stale_embeddings_repro.py`
([commit fffceaa](https://github.com/Aniruthan-0709/pathreview/commit/fffceaa)):
ingesting README v1 then an edited v2 leaves v1's text in the store.

Two related observations that shape the fix:

1. **The skip check is also non-functional.** `_check_skip` and
   `_record_ingested_source` in `pipeline.py` are placeholders — they log but
   never read/write a real `IngestedSource` row — so there is currently no
   reliable record of "have we seen this source before, and at what version?"
2. **Ingestion and the delete helper live in different abstractions.** The
   pipeline writes through `BatchEmbeddingProcessor` directly onto a raw
   ChromaDB collection, while `delete_by_source_id` lives on the `VectorStore`
   wrapper and filters on the `source_id` *metadata* field. The fix must delete
   on the same collection the pipeline writes to, and that metadata field must
   hold the stable key.

### Map

Files/functions involved:

- `ingestion/pipeline.py` — `ingest_readme`, `_hash_content`, `_check_skip`,
  `_record_ingested_source` *(primary change)*
- `ingestion/embeddings/batch_processor.py` — `process`, `_store_embedding`
  (chunk id + metadata written to Chroma)
- `rag/retriever/vector_store.py` — `delete_by_source_id` *(delete-before-add)*
- `ingestion/chunking/strategy_selector.py`, `ingestion/chunking/structural_chunker.py`
  — read-through only; they propagate metadata but shouldn't need changes
- `tests/unit/test_stale_embeddings_repro.py` — flips from failing to passing;
  add a "same content is skipped" test

Core change: split identity from version.

- **Stable `source_id`** = `{doc_type}_{profile_id}_{repo_name}` (no hash) — the
  logical key that is constant across edits.
- **`content_hash`** = `hash(content)` — stored in chunk metadata as the version
  stamp, used only for skip detection.

Re-ingest logic becomes: if a source with this stable `source_id` already exists
**and** its stored `content_hash` matches → skip. If it exists but the hash
differs → `delete_by_source_id(source_id)` first, then chunk, embed, and add the
new version.

### Plan

1. **Make `source_id` stable and add a version stamp.** In `ingest_readme`
   (and the resume/repo paths for consistency), compute
   `source_id = f"readme_{profile_id}_{repo_name}"` and compute
   `content_hash` separately. Add `content_hash` to the metadata dict so it
   lands in ChromaDB on every chunk.
2. **Detect same-vs-changed content.** Replace the placeholder skip check with a
   real one: look up existing chunks for this `source_id` (query the vector
   store, or a persisted `IngestedSource` row — see Risks) and read their stored
   `content_hash`. Same hash → return a skipped result; different or absent →
   proceed.
3. **Delete the old version before adding the new one.** When content changed,
   clear all existing chunks for the stable `source_id` (via
   `delete_by_source_id`, wired to the collection the pipeline actually writes
   to) *before* chunking/embedding the new content.
4. **Add the new version and record it.** Run the existing chunk → embed →
   store flow, then record the new `content_hash` for the source so the next
   re-ingest can compare.
5. **Prove it with tests.** The reproduction test's failing assertion should now
   pass (only v2 content remains); add a test that re-ingesting identical
   content is skipped (no delete, no re-embed) and one that a shorter v2 leaves
   no orphaned chunks.

### Inputs & outputs

- **Inputs:** `profile_id`, `repo_name`, README `content` (and `doc_type`),
  routed through `ingest_readme`.
- **Outputs / state changes:**
  - Vector store holds **exactly one** version of chunks per
    `(doc_type, profile_id, repo_name)` — the current one.
  - Editing + re-ingesting **replaces** the prior chunks (old ones deleted).
  - Re-ingesting **identical** content is a no-op (skipped; no duplicate work).
  - Each stored chunk carries a stable `source_id` plus a `content_hash` in its
    metadata.
  - `IngestResult` still reports `chunk_count` / `skipped` as before.

### Risks & unknowns

- **Where does the "current hash" live — vector store or a DB row?** The raw
  README text isn't stored in the vector DB (only chunk text + embedding +
  metadata are). Reading the hash back from chunk metadata keeps the fix inside
  the two files named in the issue and avoids depending on the broken
  `IngestedSource` bookkeeping. The more "production-correct" option is to
  actually implement `IngestedSource` persistence (a `sources` table keyed by
  `source_id` with a `content_hash` column). **Open decision** — I lean toward
  the vector-store-metadata approach to stay in scope, and will confirm before
  building.
- **Delete/add ordering (data-loss risk).** If we delete the old version and the
  embedding/add step then fails, the source is left empty — worse than stale.
  Need error handling so a failed re-ingest doesn't wipe a good prior version
  (e.g. only delete after new chunks are successfully embedded, or guard the
  sequence).
- **Two-abstraction mismatch.** `delete_by_source_id` must run against the same
  collection object the pipeline writes through; otherwise it's a silent no-op.
- **Concurrency.** Two re-ingests of the same source racing delete + add could
  interleave. Likely out of scope for #27, but worth noting.

### Edge cases

- **First ingest (no prior version):** delete is a no-op; proceed normally.
- **Identical re-ingest:** hash matches → skip; no delete, no duplicate chunks.
- **Edited content:** delete old chunks, add new.
- **New version has fewer chunks than the old one:** must delete *by source*, not
  overwrite per chunk-index, or higher-index chunks from the old version orphan
  and linger.
- **Empty / whitespace / heading-less README:** the chunker returns zero chunks;
  decide whether deleting the old version and storing nothing (source cleared) is
  acceptable, or whether such input should be rejected before deletion.
- **Same `repo_name` across different profiles:** the stable key includes
  `profile_id`, so no cross-profile collision.
- **Failed re-ingest mid-flow:** prior version should not be left in a
  half-deleted state (ties back to delete/add ordering).
