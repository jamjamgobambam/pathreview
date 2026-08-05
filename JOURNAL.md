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

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `StructuralChunker._extract_sections()` (`ingestion/chunking/structural_chunker.py`): content lines are now collected regardless of whether a heading has been seen yet, and the trailing section is always saved (guarded so purely blank/whitespace content is skipped, to avoid emitting empty chunks between adjacent headings). This resolves both the original bug (heading-less documents returning zero chunks) and the related preamble-loss defect from PLAN.md. Grepped `rag/` and `api/` for `heading_path` consumers — none exist outside the chunking module, so the empty-string sentinel for heading-less sections (`" > ".join([])`) is safe. Updated `tests/unit/test_issue_149_reproduction.py` from "expected to fail" framing to permanent regression tests; all 18 tests in that file and `test_structural_chunker.py` pass. Ran the full `tests/unit` suite and confirmed 52 pre-existing failures across unrelated modules (bias_detector, pii_scrubber, resume_parser, review_service, skill_extractor, tech_detector, etc.) are unaffected by this change — verified via `git stash` before/after comparison. `make lint`/`black` are clean on the files I touched; mypy fails repo-wide due to a pre-existing numpy/Python 3.14 stub incompatibility unrelated to this fix.

**Next steps:**
Open a draft PR, request peer/mentor review in Slack, and address feedback before marking ready for review.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/883

**Branch:** `fix/149-structural-chunker-drops-documents-with-noheader`

**What you built:**
Fixed `StructuralChunker._extract_sections()` (`ingestion/chunking/structural_chunker.py`) so it collects content lines regardless of whether a markdown heading has been seen yet, and always flushes the trailing section (skipping ones that are empty/whitespace-only). This stops heading-less documents from being silently dropped from the RAG index (`chunk()` returning `[]`) and, as a related fix, preserves preamble text that appears before a document's first heading.

**Tests added or updated:**
`tests/unit/test_issue_149_reproduction.py` — three regression tests (reframed from "expected to fail" reproduction tests now that the bug is fixed): a plain-text document with no headings produces at least one chunk, a heading-less README routed through `StrategySelector` survives the real ingestion path, and text before a document's first heading is preserved in the output rather than discarded. `tests/unit/test_structural_chunker.py::test_document_with_no_headings` (pre-existing, previously failing) now passes unchanged, confirming no regression to heading-based chunking.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(`ruff`/`black` clean on changed files; `mypy` clean on changed files. The full `tests/unit` suite and repo-wide `mypy` have pre-existing, unrelated failures — documented and confirmed via `git stash` to be identical before and after this branch; see the PR description for details.)

**Draft PR feedback received from:** none — opened directly as ready for review