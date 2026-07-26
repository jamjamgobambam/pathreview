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
