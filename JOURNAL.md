## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The structural chunker splits documents into sections using headings as
boundaries. When a document contains no headings, the chunker silently
drops it instead of falling back to a sensible default — such as treating
the entire document as a single chunk. This means valid documents with
no heading structure are never processed or stored, with no error or
warning surfaced to the caller. A successful fix would add a fallback
so heading-free documents are chunked as a whole unit rather than
discarded silently.

**Branch name:** fix/149-structural-chunker-drops-headingless-docs

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger