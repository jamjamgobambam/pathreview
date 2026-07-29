## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The structural chunker currently assumes that Markdown documents contain at least one heading. In `_extract_sections()`, text is only collected after a heading has been found, so a plain-text document without headings produces no sections. As a result, `StructuralChunker.chunk()` returns an empty list and the document is silently dropped from the ingestion process. A successful fix should preserve heading-based chunking while ensuring that headingless documents still produce one or more chunks.

**Selection notes — “Is this issue right for me?” checklist:**

This issue has a focused scope and an existing failing unit test that clearly demonstrates the expected behavior. The primary implementation is contained in `ingestion/chunking/structural_chunker.py`, with relevant tests in `tests/unit/test_structural_chunker.py`. I reproduced the issue locally by running the structural chunker test suite and confirmed that 14 tests pass while `test_document_with_no_headings` fails because the result is an empty list. The expected fix appears limited to handling the headingless-document edge case without changing the public interface or unrelated parts of the ingestion pipeline, so this is a realistic Tier 1 contribution for me.

**Branch name:** fix/149-headingless-document-chunking

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [add after committing and pushing]

**Reproduction summary:**
I reproduced issue #149 by running the existing `test_document_with_no_headings` unit test in `tests/unit/test_structural_chunker.py`. The test failed because `StructuralChunker.chunk()` returned an empty list for non-empty text without Markdown headings, causing `assert len(result) >= 1` to fail with `assert 0 >= 1`.

**PLAN.md link:** [add after creating and pushing PLAN.md]

**Walkthrough video (recommended):** Not recorded yet

**Blockers or open questions:**
I still need to determine where the fallback behavior should be implemented—entirely within `StructuralChunker`, or if another part of the chunking pipeline is also involved.


