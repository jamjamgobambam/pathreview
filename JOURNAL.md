## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The structural chunker currently assumes that Markdown documents contain at least one heading. When a document contains plain text without Markdown headings, its content is not preserved during structural chunking. The expected behavior is for non-empty headingless documents to still produce one or more chunks instead of being dropped.

**Selection notes — "Is this issue right for me?" checklist:**

This issue has a focused scope with a clear expected behavior and appears to be limited to the structural chunking logic. The primary implementation is in `ingestion/chunking/structural_chunker.py`, with corresponding unit tests in `tests/unit/test_structural_chunker.py`. Based on the issue description and code investigation, the fix should be contained to a small part of the chunking pipeline, making it an appropriate Tier 1 contribution.

**Branch name:** fix/149-headingless-document-chunking

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/daregay/pathreview/commit/<commit-hash>

**Reproduction summary:**

I reproduced issue #149 by running the existing `test_document_with_no_headings` unit test in `tests/unit/test_structural_chunker.py`. The test failed because `StructuralChunker.chunk()` returned an empty list for a non-empty document without Markdown headings, causing the assertion `assert len(result) >= 1` to fail with `assert 0 >= 1`. After tracing the code, I found that `_extract_sections()` only collects text after a heading has been found, so headingless documents produce no sections.

**PLAN.md link:** https://github.com/daregay/pathreview/blob/fix/149-headingless-document-chunking/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

I still need to determine the best way to preserve headingless documents while maintaining the existing behavior for documents that already contain headings. I also want to confirm what metadata should be assigned to chunks that do not have a heading path.

