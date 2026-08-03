## Week 7 — Issue selection

**Issue link:** [GitHub Issue Link](https://github.com/ascherj/pathreview/issues/149)

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`StructuralChunker` (the `_extract_sections` method in `ingestion/chunking/structural_chunker.py`) is a strategy for splitting documents into chunks based on Markdown headings, specifically designed to handle README-style documents. However, its collection logic relies on "first encountering a heading" before it begins recording body lines.

If the entire document contains no headings, the body lines will never be collected, and ultimately `chunk()` returns an empty list.

The problem is that this process generates no error messages or logs, resulting in such documents being silently excluded from the RAG index - users are completely unaware that their documents have "disappeared".

After the fix, headless documents should at least be retained as a single chunk (or fall back to `SemanticChunker`) rather than being discarded.

**Branch name:** fix/149-chunker-drops-no-heading-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ShiriZhang/pathreview/commit/54ff4590b6f6ceb8d561a684f2dfa8f153c20c9e

**Reproduction summary:**
Ran `pytest tests/unit/test_structural_chunker.py -k test_document_with_no_headings -v` locally; the existing test fails with `assert 0 >= 1` because `StructuralChunker.chunk()` returns an empty list for a plain-text document with no Markdown headings, confirming the behavior described in issue #149.

**PLAN.md link:** https://github.com/ShiriZhang/pathreview/blob/fix/149-chunker-drops-no-heading-docs/PLAN.md

**Walkthrough video (recommended):** Not recorded this week

**Blockers or open questions:**
Still deciding between two fix strategies (treat headless doc as one section vs. fully delegate to SemanticChunker) — plan to check linked PRs #192/#162 for precedent before finalizing in Week 9. Also spent some time confirming a pre-commit failure was pre-existing project debt rather than a fork-sync issue (documented in PLAN.md's Risks & unknowns).


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md's option (a): `_extract_sections()` now treats a headless document as a single section instead of returning an empty list. Added 3 new unit tests covering a short headless doc, a long headless doc (verifying it sub-chunks via SemanticChunker), and a false-positive heading match (`#nospace`). All 18 tests in `test_structural_chunker.py` pass, and comparing against the pre-recorded baseline confirms no new failures were introduced elsewhere in the suite (53 → 52 failing, only `test_document_with_no_headings` flipped from fail to pass).

**Next steps:**
Open PR, request peer/mentor review in Slack, finalize JOURNAL Check-in 2.

**Blockers:**
Compressed the Wednesday/Sunday check-in schedule into a single day due to limited time before the deadline.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/629

**Branch:** `fix/149-chunker-drops-no-heading-docs`

**What you built:**
Fixed `StructuralChunker.chunk()` silently dropping documents with no Markdown headings. When `_extract_sections()` finds no headings at all, it now returns the whole document as a single section instead of an empty list, so it gets chunked (and sub-chunked via `SemanticChunker` if it's large) like any other document.

**Tests added or updated:**
`tests/unit/test_structural_chunker.py` — added `test_long_document_with_no_headings_gets_sub_chunked`, `test_hash_without_space_is_not_treated_as_heading`, and `test_headless_document_has_empty_heading_metadata`, covering the fix's sub-chunking path, a false-positive heading edge case, and the resulting metadata shape.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
*(Note: this codebase has pre-existing failures unrelated to #149 — 180 ruff errors and 53 failing tests at baseline. "Passes" here means no new failures were introduced; see PR description for the full before/after comparison.)*

**Draft PR feedback received from:** Claude Code
