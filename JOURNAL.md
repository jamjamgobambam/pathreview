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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bairejavier1/pathreview/commit/f3f1dfce7664a11401adfbea7c9f149ef569cf0f

**Reproduction summary:**
Ran the reproduction script directly against StructuralChunker.chunk() with a ~1000-character headingless document and confirmed it returns 0 chunks. Also ran test_document_with_no_headings directly and confirmed it fails with assert 0 >= 1 where 0 = len([]). Traced the root cause to _extract_sections(), where a guard condition prevents any content line from being collected unless a heading has already been seen, so headingless documents never populate current_section_lines and no section is ever recorded.

**PLAN.md link:** https://github.com/bairejavier1/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** Not yet ready

**Blockers or open questions:**
Still need to confirm whether other parts of the codebase (agent/, rag/) assume heading_level is always an integer 1-6, since headingless sections will need some sentinel value there.
