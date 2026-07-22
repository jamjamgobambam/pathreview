# Module 3 Journal — PathReview Contribution

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `StructuralChunker.chunk()` method in `ingestion/chunking/structural_chunker.py` splits
documents by markdown headings to create RAG-ready chunks. When a document contains no
headings at all — such as a plain-text resume or a README with only prose — the method
returns an empty list instead of treating the full document as a single chunk. This means
heading-free documents are silently excluded from the vector index and will never be
retrieved during a review, producing incomplete feedback with no error or warning to signal
the data loss. The fix is to add a fallback at the end of `chunk()` that, when no sections
were extracted, wraps the entire document text in a single `Chunk` object and returns it.

**"Is this right for me?" checklist reasoning:**
- Scope: The change touches one method in one file (`structural_chunker.py`) plus the
  already-written test in `tests/unit/test_structural_chunker.py`. Total surface area is
  very small — well within a Tier 1 scope.
- Familiarity: The fix is pure Python with no external dependencies, no database work, and
  no API changes required.
- Reproducibility: The issue includes a three-line repro script and points to a specific
  failing test, so verifying the fix is straightforward.
- Risk: A fallback-only change can't regress documents that already have headings.
- Verdict: Good fit. Concrete problem, isolated fix, verifiable test already in place.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/nghiatra2006-jpg/pathreview/commit/10ed100f83aa69f9af826684c7d6b735bc8cc0d0

**Reproduction summary:**
Running `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings` fails with `assert 0 >= 1` — `chunk()` returns an empty list for a plain-text document because the guard in `_extract_sections()` discards all lines when `heading_stack` is empty, so no sections are ever built.

**PLAN.md link:** https://github.com/nghiatra2006-jpg/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** *(not recorded)*

**Blockers or open questions:**
Need to confirm before implementing that `strategy_selector.py` does not rely on an empty return from `chunk()` as a signal, and that `SemanticChunker` preserves `heading_path` metadata when sub-chunking the no-headings fallback section.
