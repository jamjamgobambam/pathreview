## Week 7 — Issue selection

**Issue link:** https://github.com/Sujjal1/pathreview/fix/149-structural-chunker-no-headings

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
StructuralChunker currently returns an empty chunk list for documents with no markdown headings, so plain text documents are silently excluded from the RAG index. A successful fix will ensure such documents are chunked as a single block or fall back to another strategy, preserving ingestion coverage for content without headings.

**Selection notes:**
This is a Tier 1 bug in the ingestion chunking pipeline with a clear scope and an existing failing unit test. It is a good first issue because it affects core RAG indexing behavior, is limited to `ingestion/chunking/structural_chunker.py`, and can be validated with the repository's test suite.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Sujjal1/pathreview/commit/319fb63

**Reproduction summary:**
Ran the existing test `test_document_with_no_headings` with `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings -v`, which fails with `assert 0 >= 1`. The bug is in `_extract_sections()` in `ingestion/chunking/structural_chunker.py` — when a document has no markdown headings, `heading_stack` is never populated, so the content-collection guard (`if heading_stack or current_section_lines`) prevents any lines from being captured, and the method returns an empty list. The document is silently dropped from the RAG index.

**PLAN.md link:** https://github.com/Sujjal1/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** [not yet recorded]

**Blockers or open questions:**
- Need to verify how downstream RAG retrieval consumers handle `heading_path: ""` (empty string) for headingless documents — a quick grep suggests it's stored but not used as a filter, so it should be safe.
- Should the fallback use `"(untitled)"` as the heading path, or leave it as an empty string? Leaning toward empty string to avoid injecting synthetic labels into the index.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #149 in `ingestion/chunking/structural_chunker.py`. Both sub-tasks from PLAN.md are done:
1. Added a no-headings fallback in `chunk()` — when `_extract_sections()` returns empty but the text is non-empty, the entire document is treated as a single untitled section (or delegated to `SemanticChunker` if it exceeds the 800-token limit).
2. Updated `_extract_sections()` to always collect content lines (removed the `heading_stack` guard on line 128) and to emit pre-heading content as a section with `path: []` and `level: 0`.

All 15 existing tests pass, plus 4 new edge-case tests added.

**Next steps:**
- Open draft PR for peer/mentor review
- Run full `make check` and `make test-unit` to document pre-existing vs. new failures
- Finalize PR description and submit

**Blockers:**
None — implementation is complete and all tests pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/631

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
Fixed Issue #149 where `StructuralChunker` silently dropped documents with no markdown headings. The fix modifies `_extract_sections()` to collect content lines regardless of whether a heading has been seen, and adds a fallback in `chunk()` that wraps headingless documents as a single untitled section (or delegates to `SemanticChunker` for large docs). Pre-heading content in mixed documents is now also captured.

**Tests added or updated:**
- `tests/unit/test_structural_chunker.py`: Added 4 new edge-case tests:
  - `test_no_headings_metadata_shape` — verifies `heading_path: ""` and `heading_level: 0` on headingless docs
  - `test_single_line_document` — single-line plain text returns exactly 1 chunk
  - `test_leading_text_before_first_heading` — mixed doc with pre-heading text captures both sections
  - `test_large_no_heading_document_sub_chunked` — large headingless doc triggers SemanticChunker sub-chunking

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(Note: 52 pre-existing test failures and 182 pre-existing lint errors exist across the codebase. These were present before this change and are unrelated to Issue #149. My changes introduce zero new failures — all 19 structural chunker tests pass, and no new lint/format/type errors were introduced in the files I touched.)

**Draft PR feedback received from:** [pending]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received on PR #631. As noted in the Summer 2026 course guidelines, reviewer feedback is not a feature this semester. The PR remains open against `ascherj/pathreview` with no comments or requested changes.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Understanding the implicit assumptions baked into `_extract_sections()` was harder than it looked. The bug wasn't a crash or an obvious error — it was a silent data loss issue where documents simply vanished from the RAG index without any warning. Tracing the root cause required reading through the heading-stack logic line by line to understand that the content-collection guard on line 111 (`if heading_stack or current_section_lines`) was subtly wrong: it prevented the *first* content line from ever being collected in headingless documents, because `heading_stack` was empty and `current_section_lines` was also empty at that point. The fix itself was small (removing one guard condition), but confidently identifying *which* guard to remove — without breaking headed documents — took more careful analysis than I anticipated.

**What did you learn about working in a large codebase?**
The biggest lesson was that you can't just fix the bug in isolation — you have to understand the contract between components. `StructuralChunker` feeds into `SemanticChunker` for sub-chunking, and its output metadata (`heading_path`, `heading_level`) flows downstream into the RAG retrieval layer. Before committing to `heading_path: ""` for untitled sections, I had to grep through the `rag/` module to verify that an empty string wouldn't break any filters or queries. In my own projects, I'd just pick whatever felt right and move on. In someone else's production code, you have to trace the data flow end-to-end and justify your design choice (which I documented in the PR's "Notes for Reviewers" section). I also learned to carefully distinguish pre-existing test failures (52 failures across the codebase) from anything my changes introduced — something that's never an issue in a greenfield project.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful during the planning and documentation phases — generating the structured `PLAN.md`, drafting the risk/edge-case matrices, and writing the PR description. It was also helpful for quickly scaffolding the four new test cases and ensuring they covered the right edge cases (single-line docs, pre-heading content, large doc sub-chunking). Where AI fell short was in understanding the *semantic intent* of the original code. The AI could see the `heading_stack` guard, but it couldn't tell me whether removing it would subtly break the heading hierarchy for documents that *do* have headings — that required me to manually trace through several test inputs and verify the heading-stack pop logic still worked correctly after my change. I also had to manually verify the downstream impact on the `rag/` module, which required project-specific knowledge that AI tools didn't have.

**What would you do differently if you started over?**
I would start by writing a more comprehensive reproduction test *before* reading the implementation code. I jumped into reading `_extract_sections()` immediately, but if I'd first written tests for all the edge cases (pre-heading content, single-line docs, whitespace-only docs), I would have had a clearer mental model of what "correct behavior" looks like before trying to understand what the code was actually doing. I'd also spend more time upfront understanding the full ingestion pipeline — I didn't realize until mid-implementation that `SemanticChunker` was already used for sub-chunking large sections, which meant I could reuse it for the fallback instead of writing new chunking logic.

**What are you most proud of from this module?**
I'm most proud of the defense-in-depth approach in the final implementation. The fix works at two layers: `_extract_sections()` now correctly collects pre-heading content (so headingless documents naturally produce sections), and `chunk()` has a belt-and-suspenders fallback that catches any case where `_extract_sections()` returns empty but the document has content. This means even if someone refactors `_extract_sections()` in the future and reintroduces the bug, the fallback in `chunk()` will still prevent silent data loss. Writing code that's robust against future regressions — not just today's bug — felt like a real step up in engineering maturity.
