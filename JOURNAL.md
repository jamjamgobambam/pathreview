# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The current ingestion pipeline creates new embeddings when a repository or document is updated, but older embeddings are not removed from the vector store. This can cause retrieval results to include outdated information alongside newer content. The fix should ensure that re-ingesting a source replaces or invalidates previous embeddings so retrieval only uses current data. The affected areas are the ingestion pipeline and RAG vector store components.

**Branch name:** fix/27-stale-vector-embeddings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Selection notes:
I chose this issue because it involves both backend data flow and AI/ML retrieval behavior. The scope is manageable because the problem is isolated to ingestion and vector storage, but it demonstrates understanding of RAG systems, embeddings lifecycle, and data consistency.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
PASTE_COMMIT_URL_HERE

**Reproduction summary:**
Reproduced the stale embedding behavior by re-ingesting an updated document and observing that previous vector data remained available during retrieval.

**PLAN.md link:**
https://github.com/ZainaNadeem/pathreview/blob/fix/27-stale-vector-embeddings/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm whether stale results are caused by duplicate vector insertion, missing deletion, or vector store update behavior.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1020

**Branch:** fix/27-stale-vector-embeddings

**What you built:**
Implemented a fix for stale embeddings during document re-ingestion. The ingestion pipeline now uses a stable document identifier to remove vectors from the previous document revision before storing the updated embeddings.

**Tests added or updated:**
Added `tests/unit/test_pipeline.py` with regression tests covering resume, README, and repository re-ingestion, document ID stability, deletion scoping, delete-before-add behavior, and unchanged ingestion behavior.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Verification note:** The targeted ingestion pipeline tests pass (10/10). The full repository checks report lint/formatting issues and unit-test failures outside the files changed for this contribution.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer or reviewer feedback was received on PR #1020 during this module. Reviewer
feedback is not provided for the Summer 2026 cohort, so the pull request remains open and
unreviewed. Because no review comments were raised, there were no reviewer-requested changes
to address in this iteration.

**How you responded:**
N/A — no reviewer feedback was received.

### Reflection

This was my first open-source contribution. I worked on issue #27, where the vector store kept
returning stale embeddings after a document was re-ingested. Almost all of the work happened in
`ingestion/pipeline.py`, and the part I had to understand first was how a document's existing
vectors are removed before its updated version is stored. That turned out to be the whole
problem: the pipeline derives its `source_id` from a hash of the content, so editing a document
produced a completely new identifier and the previous vectors were simply left behind, with
nothing in the pipeline ever deleting them.

The fix introduces a stable document identifier that does not change when content changes, stores
it on every chunk, and uses it to clear the previous revision's vectors before the new ones are
written. The last refinement was small: I changed the delete filter from the shorthand form
`{"document_id": document_id}` to the explicit `{"document_id": {"$eq": document_id}}`, matching
the convention already used in `rag/retriever/vector_store.py`. The work was submitted as PR #1020.

The biggest challenge was the gap between the size of the change and the effort behind it. The
final diff is small, but deciding that it was the right change took far more investigation:
reading the chunking and batch-embedding code, working out where vector IDs actually come from,
checking whether an upsert could solve it instead of a delete, and thinking through what happens
if the embedding call fails after the old vectors are already gone. Most of my time went into
understanding the surrounding behavior rather than writing lines of code.

What I learned is that contributing to an existing codebase is mostly about fitting in. I had to
follow the project's branch and commit conventions, write tests in the style already used in
`tests/unit/`, work within the dependencies the project had chosen, and stay inside the scope of
the issue. There were several things I noticed that I wanted to clean up — unsorted imports, some
outdated type annotations — and leaving them alone was the correct decision, because unrelated
changes make a pull request harder to review.

AI tools were genuinely useful for navigating unfamiliar code, thinking through possible failure
points, interpreting errors, and reasoning about the workflow. They did not replace the work. I
still had to open the real files, run the tests, check the actual behavior of the vector store
API, read the diff line by line, and judge whether a suggestion actually fit this project. Some
suggestions did not, and recognizing that was part of the exercise.

If I started again, I would narrow the issue down and trace the relevant execution path much
earlier instead of exploring broad possibilities first. I spent a while considering causes that
a careful read of the ingestion flow would have ruled out quickly.

What I am most proud of is completing the full open-source workflow for the first time: choosing
an issue, investigating a real production codebase, implementing a scoped fix, verifying the
diff, and opening a genuine pull request.