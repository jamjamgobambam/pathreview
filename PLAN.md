# Solution plan

**Issue:** [Vector store returns stale embeddings after a document is re-ingested (#27)](https://github.com/ascherj/pathreview/issues/27)

## Understand

**Expected:** Re-ingesting an edited document (e.g. a README) should *replace* that
document's chunks in the vector store, so retrieval only ever reflects the latest
version.

**Actual:** Re-ingestion is purely additive. The old chunks stay in ChromaDB
alongside the new ones, and the retriever can return stale content.

There are **two compounding root causes**:

1. **No delete-before-insert.** The ingestion pipeline only ever `.add()`s chunks.
   `VectorStore.delete_by_source_id()` exists and is even documented "for
   re-ingestion" (`rag/retriever/vector_store.py:115`), but it has **zero callers**
   — it is dead code.

2. **Identity is content-derived, so it can't be reused.** The `source_id` bakes a
   hash of the content into it
   (`ingestion/pipeline.py:143` — `f"readme_{profile_id}_{repo_name}_{hash}"`), and
   the chunk/embedding IDs inherit it
   (`ingestion/embeddings/batch_processor.py` — `f"{source_id}_chunk_{index}"`).
   An edited README therefore hashes to a **brand-new id**, so its chunks are added
   next to the old ones instead of overwriting them. Even if the delete were wired
   up, deleting by the *new* id would match nothing, because the old chunks live
   under the *old* hash.

Reproduced by running `tests/unit/test_ingestion_reingest.py`: ingest README v1
("Flask"), re-ingest v2 ("FastAPI") for the same `(profile_id, repo_name)`, and the
v1 "Flask" chunk is still present. Logs show two distinct source_ids
(`readme_P_myrepo_61bec25c…` and `readme_P_myrepo_028f6dd4…`) for the same document.

**The intended design is already visible in the schema:** the `IngestedSource`
model separates identity from version — it has `profile_id` / `source_type` /
`filename` *and* a dedicated `content_hash` column
(`core/models/ingested_source.py:38`). The pipeline just isn't honoring that
separation. This fix aligns the pipeline with the model.

## Map

Files and functions involved:

| File | Role in the fix |
|---|---|
| `ingestion/pipeline.py` | **Primary fix.** `ingest_readme` / `ingest_resume` / `ingest_repo_metadata` build the hash-in-id source_id; `_check_skip` / `_record_ingested_source` are stubs. Add a delete-before-insert step and make identity stable. |
| `ingestion/embeddings/batch_processor.py` | `_store_embedding` builds chunk IDs from `source_id`; becomes stable/idempotent once source_id is stable + delete runs first. Likely read-only, but the ID scheme is verified here. |
| `rag/retriever/vector_store.py` | Retrieval-side `delete_by_source_id` (the wrapper equivalent). Left as-is; unifying it with the pipeline path is out of scope. |
| `core/models/ingested_source.py` | No change — used as the source of truth for skip/version logic. |
| `tests/unit/test_ingestion_reingest.py` | Existing regression test (the contract). Extend to cover resume + repo paths. |

## Plan

1. **Split identity from version** (`pipeline.py`). In all three ingest methods, make
   `source_id` stable (`readme_{profile_id}_{repo_name}`, `resume_{profile_id}`,
   `repo_{profile_id}_{repo_name}`) and keep the content hash as a separate
   `content_hash`. Add `content_hash` to the chunk metadata dict so it lands on every
   chunk and in the DB record.

2. **Delete-before-insert** (`pipeline.py`). Add `_delete_existing_chunks(source_id)`
   that calls `self.vector_db.delete(where={"source_id": source_id})`, and invoke it
   immediately before `batch_processor.process(chunks)` in each method. Delete-by-
   `where` (not upsert) is chosen deliberately so it also handles the case where the
   new version has *fewer* chunks than the old, and avoids ChromaDB's duplicate-id
   error on `.add()`. **Steps 1–2 make the existing regression test pass.**

3. **Make skip logic version-aware** (`_check_skip`, `_record_ingested_source`).
   Required because with a *stable* source_id the current source_id-only skip would
   wrongly skip an *edited* document. Wire both stubs to the real `IngestedSource`
   model: skip only when a row exists with the same `source_id` **and** the same
   `content_hash`; otherwise proceed. On success, upsert the `IngestedSource` row
   (`content_hash`, `chunk_count`, `ingested_at`). Match the session's sync/async
   style used in `core/services`.

4. **Apply to all three sources without duplication.** Resume and repo-metadata
   ingestion have the identical defect. Extract the shared flow
   (`parse → metadata → delete existing → chunk → embed → record`) into one private
   `_ingest(...)` helper the three public methods call, so the bug can't reappear in
   one path.

5. **Verify & guard.** Run `make test-unit`; add regression tests mirroring the README
   test for the resume and repo paths; sanity-check that the chunker assigns a
   distinct `chunk_index` per chunk (IDs depend on it).

## Inputs & outputs

**Input:** A document being (re-)ingested — `profile_id`, a document identity
(`repo_name` for README/repo), and its `content` — plus the existing vector-store
collection and DB session.

**Output / change of behavior:**
- Before writing new chunks, all prior chunks for that stable `source_id` are removed
  from the vector store.
- After ingestion, the store contains **only** the current version's chunks; the
  `IngestedSource` row reflects the latest `content_hash` and `chunk_count`.
- Unchanged content (same hash) is skipped; changed content replaces cleanly.
- No behavioral change to retrieval APIs — only the data they read over is now clean.

## Risks & unknowns

- **Existing/legacy data.** Chunks already stored under old hash-based source_ids
  won't match the new stable ids, so future re-ingests won't clean them up. Need a
  decision: one-time reset of `.chromadb` in dev, or a small backfill/migration
  script. Flag before shipping.
- **Sync vs. async DB session.** `core/services` uses `await db.delete(...)`, but the
  pipeline's `db_session` usage is unclear. Must confirm which it is before wiring
  Step 3, or `_check_skip`/`_record_ingested_source` will break at runtime.
- **Collection wiring mismatch.** Ingestion uses `vector_db` as a *raw* ChromaDB
  collection (`batch_processor` calls `.add()`), while retrieval goes through the
  `VectorStore` wrapper with `collection_name = profile_{id}` (`rag/retriever/hybrid.py:42`).
  The delete must target the same collection ingestion writes to. Confirm the two
  sides agree on collection identity, or stale chunks could persist in a different
  collection than the one queried.
- **`chunk_index` uniqueness.** If the chunker ever omits `chunk_index`, every chunk
  collapses to `..._chunk_0` and overwrites itself. Not the reported bug, but adjacent
  — worth verifying.

## Edge cases

- **Re-ingest with identical content** → skip (same hash); no delete, no rewrite.
- **Re-ingest with fewer chunks than before** → old surplus chunks fully removed
  (why delete-by-`where` beats upsert).
- **First-ever ingest** (nothing to delete) → delete is a no-op, must not error.
- **Delete failure / partial vector-store error** → log and surface safely without
  corrupting state (don't leave half-deleted-then-added chunks silently).
- **Two different documents sharing a profile** (e.g. two repos) → deletes are scoped
  by full `source_id`, so re-ingesting one repo must not touch another's chunks.
- **Same repo name across different profiles** → `profile_id` is part of the id, so no
  cross-profile collision.
