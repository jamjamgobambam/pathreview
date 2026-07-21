## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

Choosing Tier-1 since this is my first open-source contribution. Potential second issue after this is implemented: https://github.com/ascherj/pathreview/issues/44

**Problem summary:**
The structural chunker splits documents into sections using headings as
boundaries. When a document contains no headings, the chunker silently
drops it instead of falling back to a sensible default — such as treating the entire document as a single chunk. This means valid documents with no heading structure are never processed or stored, with no error or warning surfaced to the caller. A successful fix would add a fallback so heading-free documents are chunked as a whole unit rather than discarded silently.

We have a failing test `test_document_with_no_headings` in `tests/unit/test_structural_chunker.py.`. Once the correct fix is applied, it can be verified with this existing test.

**Branch name:** fix/149-structural-chunker-drops-headingless-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

