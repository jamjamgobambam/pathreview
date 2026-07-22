## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings
 #]

**Tier:** [*] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[structuralchunker.chunk() returns an empty list for any document without markdown headings. so the entire document is silently excluded from the RAG index instead of being chunked as a single block. IOr also falling back to another strategy.]

**Branch name:** [fix/149-structural-chunker-drops-documents-with-noheader]

**Setup confirmation:** [ yes] App runs locally at localhost:5173

**Cohort ledger:** [ yes ] Issue added to cohort ledger