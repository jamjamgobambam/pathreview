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

**PR link:** https://github.com/ascherj/pathreview/pull/382

**Branch:** `fix/27-vector-store-stale-embeddings-error`

**What you built:**
Re-ingestion now replaces a document's chunks instead of accumulating them: `source_id` is a
stable identity (profile/repo) with the content hash carried separately, and a document's
existing chunks are deleted before the new ones are written, so the retriever can no longer
surface stale embeddings.

**Tests added or updated:**
`tests/unit/test_ingestion_reingest.py` — README replacement (reproduction) plus resume,
repo-metadata, chunk-shrink, identical-content, and sibling-source cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(In this repo both commands have documented pre-existing failures; "passes" here
means my changes introduce no new failures — verified: test-unit went 54→53 failing
with +6 of my tests passing, and ruff went 182→181 errors. Details in the PR.)_

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in on PR #382 (https://github.com/ascherj/pathreview/pull/382) — as
of the end of the week it has no reviews and no comments (review status still
`REVIEW_REQUIRED`). Per the Summer 2026 note, reviewer feedback isn't part of this
cohort, so this is expected; I'm noting it and moving on. The PR is open and marked ready
for review (not a draft) so it's in a reviewable state if feedback does arrive later.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Navigating the codebase was harder than the fix itself. The issue pointed at two files
(`rag/retriever/vector_store.py` and `ingestion/pipeline.py`), but understanding the *real*
cause meant tracing a chain I couldn't see from the issue text: `ingest_readme` →
`batch_processor.process` → `_store_embedding`, and how the chunk IDs were actually built.
The bug turned out to be trickier than "the store isn't cleared" — it was two compounding
causes (a dead `delete_by_source_id` that nothing called, *and* a `source_id` that baked
the content hash in, so the same document could never be identified across edits). I also
hit surprises that had nothing to do with my change: `make check` and `make test-unit`
already failed on 180+ pre-existing lint/type errors and ~54 failing tests, so I had to
figure out what "passing" even means in a repo that doesn't pass, and the pipeline wasn't
wired into any route yet, so I couldn't just run the app end-to-end to watch the bug.

**What did you learn about working in a large codebase?**
Even after learning the workflow, it's still hard to know what the *correct* fix is —
which was the biggest shift from building my own projects. In my own code I hold the whole
design in my head; here I had to infer intent from the code and the data model. The turning
point was noticing the `IngestedSource` model already separated identity from version (it
has both a stable identity and a dedicated `content_hash` column) — that told me the
"right" fix was to make the pipeline honor a design that already existed, not invent a new
one. I also learned that scope discipline matters more here: I deliberately left the
async-DB wiring and a schema migration as documented follow-ups instead of expanding the
PR, and that I'm responsible for proving I didn't make things worse (baseline vs. after
counts) rather than fixing the whole repo.

**How did AI tools help — and where did they fall short?**
AI was most useful for building an accurate mental model fast — tracing the call chain,
and correcting my first wrong theory. Initially I thought the bug was that *old DB info
wasn't being re-vectorized*, so stale info lingered on update; working through the code
with AI, I understood it was the opposite — the new content *was* vectorized fine, but
under a brand-new hash-based ID, so the old vectors were never replaced. Where AI fell
short: it couldn't tell me the project's own conventions or the state of the repo. I had to
run the tools myself to learn that `make check` uses `black .` (which would rewrite the
whole file), that the failures were pre-existing, and that the pipeline was unwired — and I
had to make the judgment calls (bypass hooks with `--no-verify` and document it; keep the
diff focused; where to draw the scope line). AI proposes; verifying against the actual repo
was on me.

**What would you do differently if you started over?**
I'd reproduce with a failing test *first*, before reading deeply — writing the
`test_ingestion_reingest.py` case is what made the two root causes concrete, and I'd reach
for that earlier as a diagnosis tool, not just a regression guard. I'd also check the
repo's baseline `make check` / `make test-unit` state on day one so I wasn't surprised by
pre-existing failures mid-implementation. Issue selection I'd keep — a well-scoped Tier 3
bug in the area I wanted to learn (ingestion ↔ vector storage) was the right call.

**What are you most proud of from this module?**
Not stopping at the surface fix. It would have been easy to wire up the existing
`delete_by_source_id` and call it done — but that alone wouldn't have worked, because the
content-hash-in-ID meant there was no stable identity to delete by. Digging until I
understood *why* the obvious fix fails, then aligning the pipeline with the data model's
existing intent and proving it with edge-case tests (chunk-shrink, identical-content,
sibling-source isolation), is the thing I'm proudest of.
