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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed the root-cause investigation from PLAN.md: traced the bug to the guard condition in `_extract_sections()` that only collected content lines once `heading_stack` was non-empty. Implemented the fix by replacing that guard with a content-based check, allowing headingless documents to be captured as a section. Verified the fix resolves the original repro (`chunk()` now returns 1 chunk instead of 0 for a headingless document) and confirmed all pre-existing tests in `test_structural_chunker.py` still pass.

**Next steps:**
Add a new test covering a headingless document that also exceeds `SECTION_TOKEN_LIMIT`, to confirm the `SemanticChunker` sub-chunking fallback works correctly for this case too. Then run `make check` and `make test-unit` for full self-review, document any pre-existing failures, and open the PR.

**Blockers:**
None — the fix ended up being narrower in scope than expected once the root cause was clear.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/578

**Branch:** fix/149-structural-chunker-no-headings

**What you built:**
Fixed `StructuralChunker._extract_sections()` so documents with no markdown headings are no longer silently dropped from the RAG index. The fix replaces a guard condition that depended on heading state with one that checks for actual accumulated content, so headingless documents are now captured as a section (using `heading_path=""` and `heading_level=0` as sentinel values) instead of producing an empty chunk list.

**Tests added or updated:**
Added `test_large_document_with_no_headings_is_sub_chunked` in `tests/unit/test_structural_chunker.py`, covering the case where a headingless document also exceeds `SECTION_TOKEN_LIMIT` and must be routed through `SemanticChunker` rather than returned as a single oversized chunk. The pre-existing `test_document_with_no_headings` test (previously failing) now passes without modification.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both commands surface pre-existing, unrelated failures documented in the PR description — 52 pre-existing test failures across unrelated modules and 182 pre-existing lint errors repo-wide, plus a pre-existing mypy/NumPy stub incompatibility. This change introduces no new failures in any of the three.)*

**Draft PR feedback received from:** none
