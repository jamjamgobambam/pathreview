## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `StructuralChunker` class is responsible for splitting documents into
smaller pieces ("chunks") before they're added to the RAG index, so the app
can search and retrieve relevant sections later. Right now, it only knows how
to split documents that have markdown headings — if a document has no
headings at all, the chunker returns an empty list instead of treating the
whole document as one chunk or falling back to a different splitting
strategy. This means any heading-less document is silently dropped from the
index entirely, so its content becomes invisible to search and retrieval,
with no warning or error to indicate anything went wrong. A successful fix
would make `StructuralChunker.chunk()` return at least one chunk for these
documents, likely by adding a fallback path when no headings are detected,
and there's already a failing test (`test_document_with_no_headings`) that
should pass once the fix is correct.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger