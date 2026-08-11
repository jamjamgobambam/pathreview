## Week 7 – Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1 [ ] Tier 2 [x] Tier 3

**Problem summary:**  
When an existing document is re-ingested, the application does not fully replace the document's previous vectors. As a result, the vector store can continue returning outdated chunks and embeddings from the older version of the document. A successful fix would remove or replace the old vectors before storing the newly generated embeddings, ensuring retrieval results always reflect the latest document content.

**Selection notes:**  
I chose this issue because I have previously worked with document ingestion in the Unofficial Guide project, so I already understand the general ingestion workflow. The issue is focused enough to investigate while also helping me improve my understanding of vector stores and RAG systems. I will likely need to trace how document IDs, chunks, and vector-store records are handled during re-ingestion.

**Branch name:** `fix/27-stale-embeddings`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---


# Week 8 – Reproduction

## Reproduction summary

I created a new unit test to reproduce Issue #27 by ingesting a document, modifying its contents, and re-ingesting it using the same `source_id`. The expected behavior was that the vector store would replace the old document with the updated one.

## Test performed

1. Created a document with the text:
   - "Original document says Python."
2. Ingested the document into the vector store.
3. Updated the document text to:
   - "Updated document says Rust."
4. Re-ingested the document using the same `source_id`.
5. Queried the stored document from the vector store.

## Result

The test failed because the vector store still returned the original document instead of the updated one.

**Expected:**

```
Updated document says Rust.
```

**Actual:**

```
Original document says Python.
```

This confirms that stale embeddings remain after re-ingesting a document and successfully reproduces Issue #27 in my local environment.

## Files investigated

- `tests/unit/test_batch_processor.py`
- `ingestion/embeddings/batch_processor.py`
- `ingestion/embeddings/provider.py`
- `rag/vector_store.py`

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I reproduced Issue #27 by creating a regression test that re-ingests a document using the same `source_id`. After tracing the embedding storage workflow, I identified that `BatchEmbeddingProcessor` was using ChromaDB's `add()` method to store embeddings. I updated the implementation to use `upsert()`, allowing existing embeddings to be replaced during re-ingestion. The targeted regression test now passes.

**Next steps:**
Complete the pull request, update the journal with the PR link, and submit the branch URL.

**Blockers:**
The full unit test suite contains unrelated pre-existing collection errors in other test modules. The targeted regression test for this issue passes after the fix.

---

### Check-in 2

**PR link:** https://github.com/ascherj/pathreview/pull/702

**Branch:** `fix/27-stale-embeddings`

**What you built:**
Updated `BatchEmbeddingProcessor` to use ChromaDB's `upsert()` operation instead of `add()` when storing embeddings. This ensures that re-ingesting a document with the same embedding ID replaces the previously stored document instead of leaving stale embeddings in the vector store.

**Tests added or updated:**
Updated `tests/unit/test_batch_processor.py` by adding a regression test (`test_reingestion_replaces_existing_document`) that verifies re-ingesting a document with the same `source_id` replaces the stored document with the updated version.

**Self-review confirmation:**  
[ ] make check passes  
[ ] make test-unit passes

**Draft PR feedback received from:** none

**Testing notes:**
The targeted regression test
`tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_reingestion_replaces_existing_document`
passes. The full unit suite is blocked by seven unrelated collection errors in existing test modules.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
The grader said that changing `add()` to `upsert()` in `BatchEmbeddingProcessor._store_embedding` was a clean and targeted fix that addressed the root cause of Issue #27. The grader also said that my regression test correctly reproduced the reported bug and verified the behavior after the fix. One area for improvement was test coverage: I identified edge cases in `PLAN.md`, such as re-ingesting documents with more or fewer chunks, but did not add tests for those cases. The grader also recommended documenting exactly which pre-existing tests failed before and after my change.

**How you responded:**
I reviewed the feedback and agree that the edge cases identified in my plan should have been converted into additional tests. If I continued working on this issue, I would add tests for re-ingesting documents with different numbers of chunks and compare the pre-existing test failures before and after the implementation. This would provide stronger evidence that the fix handles more than the basic regression case and does not introduce unrelated regressions.

---

### Reflection

**What was harder than you expected?**
Reproducing the stale embeddings issue was harder than I expected because my first test attempt failed because of my local ChromaDB setup rather than Issue #27 itself. I had to distinguish environment-related failures from the actual application bug before I could create a useful regression test. Once I reproduced the real issue, I confirmed that the original document remained in the vector store after re-ingestion.

**What did you learn about working in a large codebase?**
I learned that understanding the existing flow is more important than immediately changing code. For Issue #27, I traced the behavior through components such as `batch_processor.py`, `provider.py`, and the vector-store code before identifying where the stale data originated. The final implementation change was very small, but finding the correct place to make that change required much more investigation.

**How did AI tools help — and where did they fall short?**
AI tools helped me understand unfamiliar parts of PathReview, interpret test failures, and narrow down which components were relevant to the stale embeddings problem. They also helped me understand the difference between ChromaDB's `add()` and `upsert()` behavior. However, I still needed to run the code myself and inspect the results because not every failure was caused by my implementation, especially the environment and pre-existing test-suite failures.

**What would you do differently if you started over?**
If I started over, I would create the smallest regression test earlier and establish a clear baseline before changing the implementation. Based on the grader's feedback, I would also turn the edge cases I identified in `PLAN.md` into actual tests, especially re-ingesting documents with more or fewer chunks. I would also record the exact pre-existing test failures before making the change so I could compare them afterward.

**What are you most proud of from this module?**
I am most proud that I took Issue #27 from investigation to an actual pull request. I reproduced the stale embeddings behavior, traced the root cause to the embedding storage logic, changed ChromaDB from `add()` to `upsert()`, and confirmed that my regression test passed afterward. I am also proud that the grader specifically recognized the fix as a clean, targeted change that directly addressed the root cause.