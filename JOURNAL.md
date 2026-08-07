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

**Reproduction commit link:**  https://github.com/daregay/pathreview/commit/3ca92ba

**Reproduction summary:**

I reproduced issue #149 by running the existing `test_document_with_no_headings` unit test in `tests/unit/test_structural_chunker.py`. The test failed because `StructuralChunker.chunk()` returned an empty list for a non-empty document without Markdown headings, causing the assertion `assert len(result) >= 1` to fail with `assert 0 >= 1`. After tracing the code, I found that `_extract_sections()` only collects text after a heading has been found, so headingless documents produce no sections.

**PLAN.md link:** https://github.com/daregay/pathreview/blob/fix/149-headingless-document-chunking/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

I still need to determine the best way to preserve headingless documents while maintaining the existing behavior for documents that already contain headings. I also want to confirm what metadata should be assigned to chunks that do not have a heading path.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix for Issue #149 in `ingestion/chunking/structural_chunker.py`. When a non-empty document contains no Markdown headings, the structural chunker now creates a fallback section containing the document text instead of returning an empty list. The existing heading-based chunking behavior remains unchanged.

**Next steps:**
I will finish verifying the implementation, document the repository’s pre-existing lint and unit-test failures, commit and push my changes, open a pull request, and complete the final Week 9 check-in with the PR link.

**Blockers:**
The full `make check` and `make test-unit` commands report several pre-existing failures in unrelated parts of the repository. The focused structural chunker test suite passes all 15 tests, including the headingless-document case.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/617

**Branch:** `fix/149-headingless-document-chunking`

**What you built:**
I fixed Issue #149 by updating the structural chunker to handle non-empty documents without Markdown headings. When no structural sections are found, the chunker now creates a fallback section so the document content is preserved while maintaining the existing behavior for heading-based documents.

**Tests added or updated:**
I updated `tests/unit/test_structural_chunker.py` to strengthen the headingless document test by verifying the returned chunk, preserved content, source metadata, `heading_path`, and `heading_level`. I also added assertions to existing heading path tests to satisfy lint requirements.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both required commands were run and reviewed. The repository contains pre-existing failures in unrelated modules, but this contribution introduced no new failures. All 15 tests in `tests/unit/test_structural_chunker.py` pass, and the modified files pass Ruff and Black.

**Draft PR feedback received from:** none


## Week 10 — Iteration & Reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback was received before the end of the course. My pull request remains open and available for review.

**How you responded:**

N/A

---

### Reflection

**What was harder than you expected?**

Understanding the existing codebase was much harder than writing the actual fix. Even though my issue was relatively small, I first had to understand how the structural chunker interacted with semantic chunking, how metadata was preserved, and how the existing unit tests were organized. It took time to trace the flow before I felt confident making changes.

**What did you learn about working in a large codebase?**

I learned that making even a small change requires understanding the surrounding system. Instead of immediately writing code, I spent time reading existing implementations, following established patterns, and making sure my solution fit naturally with the rest of the project. I also learned that tests are just as important as the implementation because they document expected behavior and help prevent regressions.

**How did AI tools help — and where did they fall short?**

AI was extremely helpful for navigating an unfamiliar codebase, explaining functions, identifying where logic lived, and helping me reason through possible solutions. It also helped me understand the project's architecture much faster than reading everything from scratch. However, AI could not determine the correct solution on its own. I still had to verify its suggestions by reading the code, reproducing the issue myself, running tests, and ensuring that my implementation followed the project's conventions rather than simply accepting generated code.

**What would you do differently if you started over?**

If I started over, I would spend more time understanding the codebase before trying to implement a solution. Early on, I focused on the specific issue too quickly instead of first building a mental model of how the chunking pipeline worked. I would also open my pull request earlier to allow more time for discussion and any potential reviewer feedback.

**What are you most proud of from this module?**

I'm most proud that I completed an end-to-end open source contribution using a real development workflow. From selecting an issue and reproducing the bug to planning, implementing the fix, writing tests, documenting my work, and submitting a professional pull request, I experienced the complete contribution process instead of working on an isolated assignment.

