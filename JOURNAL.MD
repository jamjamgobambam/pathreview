## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/27]

**Issue title:** [https://github.com/ascherj/pathreview/issues/27]

**Tier:** [ ] Tier 1  [ ] Tier 2  [ X ] Tier 3

**Problem summary:**
When a vector database returns stale embeddings after a document is re-ingested, it means that there are old or stale chunks that don't accurately reflect the new document's chunks. This can lead to incorrect information being retrieved in the retrieval step of the RAG pipeline. this issue takes place in the /rag/retriever/vector_store.py part of the project. 

**Branch name:** [fix/27-vectordb-stale-embeddings]

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [9455a8f](https://github.com/amalrajn/pathreview/commit/9455a8faa13fb929f2d8904eb88bba4915167f4c)

**Reproduction summary:**
I added an integration test ([tests/integration/test_stale_embeddings_repro.py](https://github.com/amalrajn/pathreview/blob/fix/27-vectordb-stale-embeddings/tests/integration/test_stale_embeddings_repro.py)) that mirrors the pipeline's id scheme — `source_id` embeds the content hash, so an edited README gets a new id, and `VectorStore.delete_by_source_id` is never called. After ingesting a README that says "Flask" and then a re-ingested version that says "FastAPI", I observed both chunks coexisting in the ChromaDB collection and a query returning the stale "Flask" chunk.

**PLAN.md link:** [PLAN.md](https://github.com/amalrajn/pathreview/blob/fix/27-vectordb-stale-embeddings/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm which write path production actually uses — `batch_processor._store_embedding` calls `vector_db.add(...)` directly, while `VectorStore.add_chunks` reads chunk attributes that the `Chunk` dataclass doesn't have — before finalizing the stable-id/delete scheme.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Resolved the Week 8 blocker first: confirmed the pipeline's real write path is
`batch_processor._store_embedding` → the raw ChromaDB collection (it stores
`chunk.metadata` wholesale), while `VectorStore.add_chunks` is unused dead code
that reads attributes `Chunk` doesn't have. That settled the id/delete scheme.

Done from PLAN.md:
- **Sub-task 1 (stable document key):** each source now derives a
  content-independent `document_id` (e.g. `readme_{profile_id}_{repo_name}`) and
  keeps `source_id = {document_id}_{content_hash}` (unchanged string). Added
  `document_id` to every chunk's metadata. ([ingestion/pipeline.py](ingestion/pipeline.py))
- **Sub-task 2 (delete-before-insert):** added `_delete_existing_chunks(document_id)`
  and call it before `batch_processor.process(...)` in all three ingest paths
  (readme/resume/repo).
- **Sub-task 3 (align id/metadata scheme):** deletion filters on the `document_id`
  metadata the write path stores, so the delete actually matches stored rows;
  added `VectorStore.delete_by_document_id` as the retriever-side primitive.
- **Sub-task 4 (skip logic):** moved the "already ingested" check onto the vector
  store (`source_id` lookup) instead of the non-functional `db_session`
  placeholder, so unchanged content is still skipped.
- **Sub-task 5 (regression test):** inverted the reproduction into a regression
  test and added focused unit tests. All new tests pass.

**Next steps:**
Open the draft PR, request peer review in Slack, and finalize the PR description
once feedback is in.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/PENDING _(to be replaced with the live PR URL on submission)_

**Branch:** `fix/27-vectordb-stale-embeddings`

**What you built:**
The ingestion pipeline now tags every chunk with a stable, content-independent
`document_id` and deletes that document's existing chunks before storing a new
version, so re-ingesting an edited README (or resume/repo metadata) fully
replaces the old chunks instead of leaving them behind — the retriever can no
longer return stale content (issue #27).

**Tests added or updated:**
- `tests/unit/test_ingestion_pipeline.py` (new) — drives the real pipeline against
  an in-memory ChromaDB collection with `MockEmbeddingProvider`; covers that
  re-ingestion evicts the stale chunk, retrieval can't return stale content,
  unchanged content is skipped, first-ingest delete is a safe no-op, a shrinking
  README leaves no leftover chunks, and re-ingestion is isolated per profile.
- `tests/unit/test_vector_store.py` (new) — covers `delete_by_document_id`
  (removes all versions of one document, leaves other documents, no-op on
  missing/empty collection) and that `delete_by_source_id` only removes the exact
  content version targeted.
- `tests/integration/test_stale_embeddings_repro.py` (updated) — the Week 8
  reproduction, inverted into a regression test asserting only the current README
  survives, plus a skip-unchanged case.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(Documented pre-existing failures: on a clean checkout `make test-unit` reports
53 failing tests and `make check` fails at `ruff` (182 findings) and `mypy`
(untyped-defs repo-wide + a numpy stub error). After my change the unit failure
count is still 53 (same set) and ruff is still 182 — my changes introduce no new
failures, which is the bar for "passes" in a codebase with documented
pre-existing failures.)_

**Draft PR feedback received from:** none (pending — will request in the cohort Slack channel)