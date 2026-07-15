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
