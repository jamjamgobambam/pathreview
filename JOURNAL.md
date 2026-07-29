# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The RAG system stores document embeddings in a vector store so the retriever
can find relevant chunks. When a document such as a README is edited and sent
back through the ingestion pipeline, the pipeline writes the new embeddings but
never removes the document's previous ones, so both versions coexist in the
store. Because of this, the retriever can surface outdated chunks that no longer
match the document's current content. A successful fix makes re-ingestion
idempotent — clearing or overwriting a document's existing embeddings before
writing the new ones — so retrieval always reflects the latest version. This
affects the RAG layer, specifically `rag/retriever/vector_store.py` and
`ingestion/pipeline.py`.

**Selection reasoning:**
I chose this as a Tier 3 issue because I am still building my comfort with the
RAG layer, and this bug is well-scoped rather than open-ended. It is isolated to
two files (`rag/retriever/vector_store.py` and `ingestion/pipeline.py`), it has a
clear reproduction path (edit and re-ingest a document, then observe stale chunks
in retrieval), and the maintainer's 6–9 hour estimate suggests a fix that is
ambitious enough to stretch me but bounded enough to finish within Module 3. It
also lines up with what I want to learn this module — how ingestion and vector
storage interact — so the scope fits both my current skill level and my goals.

**Branch name:** fix/27-vector-store-stale-embeddings-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/xulinxi/pathreview/commit/ff16ecb

**Reproduction summary:**
I reproduced the bug with a unit regression test (`tests/unit/test_ingestion_reingest.py`)
that ingests a README ("Flask"), then re-ingests an edited version ("FastAPI") for the
same `(profile_id, repo_name)`. The old "Flask" chunk survives alongside the new one and
the test fails; the logs show the two versions landing under different content-hash-based
source_ids (`readme_P_myrepo_61bec25c…` vs `readme_P_myrepo_028f6dd4…`), confirming the
pipeline adds rather than replaces.

**PLAN.md link:** https://github.com/xulinxi/pathreview/blob/fix/27-vector-store-stale-embeddings-error/PLAN.md

**Blockers or open questions:**
Two things to resolve before coding in Week 9: (1) whether the pipeline's `db_session` is
sync or async (affects how I wire the real skip/record logic), and (2) how to handle
legacy chunks already stored under old hash-based ids — dev reset of `.chromadb` vs. a
backfill script.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix is implemented and all six regression tests pass (`make test-unit`: 53 failed /
381 passed — same pre-existing failures as baseline, +6 of my tests now passing, zero new
failures). Done from PLAN.md: stable `source_id` split from `content_hash` (Step 1),
delete-before-insert via `_delete_existing_chunks` (Step 2), and version-aware skip keyed
on `content_hash` (Step 3), all applied to the resume, README, and repo-metadata paths
(Step 4). Expanded the regression suite (Step 5) to cover all three paths plus chunk-
shrink, identical-content idempotency, and sibling-source isolation.

Resolved my Week 8 open questions: (1) the whole app is async, but `IngestionPipeline` is
synchronous and not yet wired into any route, so I kept the skip/record logic sync to match
the existing stub and the test's mock; (2) `IngestedSource` has no `source_id` column, so
durable persistence of the stable id is a documented follow-up rather than part of this fix.

**Next steps:**
Self-review against `docs/CONTRIBUTING.md`, open a draft PR, and request peer feedback in
Slack. Document the pre-existing `make check` / `make test-unit` failures in the PR body and
confirm my changes introduce none.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** _[add when PR is opened]_

**Branch:** `fix/27-vector-store-stale-embeddings-error`

**What you built:**
Re-ingestion now replaces a document's chunks instead of accumulating them: `source_id` is a
stable identity (profile/repo) with the content hash carried separately, and a document's
existing chunks are deleted before the new ones are written, so the retriever can no longer
surface stale embeddings.

**Tests added or updated:**
`tests/unit/test_ingestion_reingest.py` — README replacement (reproduction) plus resume,
repo-metadata, chunk-shrink, identical-content, and sibling-source cases.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** _[name or Slack handle, or "none"]_
