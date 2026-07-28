## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings
]

**Tier:** [#] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The function, StructuralChunker.chunk(), returns an empty list for any document without markdown headings, and it removes the entire document from the RAG index instead of being it chunked as a single block or falling back to another strategy. I will reproduce the error and then work with the test_document_with_no_headings in tests/unit/test_structural_chunker.py to show a successful fix

**Branch name:** [149-structural-chunker-silently-drops-documents-that-contain-no-headings]

**Setup confirmation:** [#] App runs locally at localhost:5173

**Cohort ledger:** [#] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e422a33](https://github.com/folusho-adeyemi/pathreview/commit/e422a33bff82ece44e63c35db4ac256909524e05)

**Reproduction summary:**
Ran `StructuralChunker().chunk("This is a plain document with no headings at all. " * 20, {})` and it returned 0 chunks, and `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings` failed with `assert 0 >= 1`. Root cause: `_extract_sections()` only collects content and emits a section once a heading has been seen (`if heading_stack ...`), so a document with no headings never populates `heading_stack` and produces no sections. I documented this at the exact guard in `ingestion/chunking/structural_chunker.py`.

**PLAN.md link:** [PLAN.md](https://github.com/folusho-adeyemi/pathreview/blob/149-structural-chunker-silently-drops-documents-that-contain-no-headings/PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Need to confirm whether any downstream consumer of the RAG index assumes a non-empty `heading_path` before committing to `heading_path == ""` for heading-less documents (vs. falling back to the source name). This file also has pre-existing ruff/mypy failures that the Week 9 fix commit will need to clean up.