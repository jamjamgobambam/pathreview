## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/149]

**Issue title:** [Structural chunker silently drops documents that contain no headings]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[The StructuralChunker used by the ingestion pipeline currently fails to create chunks when a document does not contain markdown headings. In ingestion/chunking/structural_chunker.py, the _extract_sections() helper only captures content after detecting a heading, causing heading-free documents to return no chunks even when they contain valid text. This affects README ingestion because StructuralChunker is selected for README documents through the ingestion pipeline. A successful fix would ensure that any non-empty document can still produce at least one chunk while preserving the current behavior for empty documents.]

**Branch name:** [fix/149-structural-chunker-fallback]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Issue selection notes ("Is this right for me?" checklist):**
[I chose this issue because it is my first open source contribution and I wanted to start with a manageable Tier 1 bug. I was able to understand the problem, locate the affected ingestion and chunking files, and identify what the expected behavior should be after the fix. The issue has clear reproduction steps and a related test, which makes it a good fit for learning how to contribute to a larger codebase while keeping the scope realistic for the project timeline.]