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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/flyingtony1424/pathreview/commit/1428e97b5db37ca2b1dedac442c6374a4627eb90]

**Reproduction summary:**
[Reproduced with failing unit tests: `StructuralChunker.chunk()` returns an empty list for any non-empty document without markdown headings, and `StrategySelector.chunk()` with `source_type="readme"` therefore produces 0 chunks for a heading-less README (silently dropped from the RAG index). Ran `.venv/Scripts/python -m pytest tests/unit/test_issue_149_reproduction.py -v` — 3 tests fail as expected, including a related defect where preamble text before the first heading is also lost.]

**PLAN.md link:** [https://github.com/flyingtony1424/pathreview/blob/fix/149-structural-chunker-drops-documents-with-noheader/PLAN.md]

**Walkthrough video (recommended):** [to be added]

**Blockers or open questions:**
[Deciding what `heading_path` should be for heading-less chunks (empty string vs. a sentinel like the doc title) — need to check how retrieval/citation code in `rag/` consumes `heading_path`. Also unsure whether previously ingested heading-less docs need re-ingestion after the fix, since they currently have zero chunks in the index.]