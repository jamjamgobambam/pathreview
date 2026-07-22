## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
StructuralChunker currently returns an empty chunk list for documents with no markdown headings, so plain text documents are silently excluded from the RAG index. A successful fix will ensure such documents are chunked as a single block or fall back to another strategy, preserving ingestion coverage for content without headings.

**Selection notes:**
This is a Tier 1 bug in the ingestion chunking pipeline with a clear scope and an existing failing unit test. It is a good first issue because it affects core RAG indexing behavior, is limited to `ingestion/chunking/structural_chunker.py`, and can be validated with the repository's test suite.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
