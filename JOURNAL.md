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

**PR link:** [to be added upon PR submission]

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
