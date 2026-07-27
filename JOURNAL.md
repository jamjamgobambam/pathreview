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
