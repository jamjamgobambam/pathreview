## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The structural chunker doesn't handle documents that don't contain Markdown headings. Instead of creating at least one chunk, it returns an empty list, so those documents are skipped, and they never make it into the RAG index. This affects the ingestion pipeline because plain text documents cannot be processed correctly.

A successful fix would make sure documents without headings still get chunked, such as by treating the whole document as a single chunk or using a fallback approach.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/goodCodeForGood/pathreview/commit/<reproduction-commit>

**Reproduction summary:**

I reproduced the issue by running the structural chunker against a Markdown document containing only plain text and no Markdown headings. The chunker returned an empty list instead of generating a fallback chunk, causing the document to be skipped by the ingestion pipeline.

**PLAN.md link:** https://github.com/goodCodeForGood/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Blockers or open questions:**

I still need to verify whether the fallback chunk should include the same metadata as heading-based chunks and whether any downstream components rely on heading information.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the structural chunker fix for documents without Markdown headings. Updated the structural chunker tests to verify heading-less documents, heading paths, metadata, nested headings, and other section-handling behavior. I also addressed the necessary type annotations and linting issues in the chunking code and tests.

**Next steps:**
Run the full project checks, review the final diff, commit and push the changes, and open the PR for review. I will also complete the final self-review and document the test results.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/266

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
Fixed the structural chunker so documents without Markdown headings are handled correctly instead of producing no usable chunks. The implementation preserves the expected chunk metadata while continuing to support heading-based structure and nested heading paths.

**Tests added or updated:**
Updated `tests/unit/test_structural_chunker.py` with coverage for heading-less documents, whitespace-only input, nested headings, heading paths and breadcrumbs, heading levels, metadata preservation, large sections, multiple H1 headings, and empty sections. The structural chunker test suite passes with **15/15 tests passing**.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

Pre-existing failures were observed in the broader chunk-related unit test run for BatchEmbeddingProcessor and FaithfulnessChecker. These failures are unrelated to the structural chunker changes. The structural chunker tests pass, and make check and make test-unit pass.

**Draft PR feedback received from:** None as of now
