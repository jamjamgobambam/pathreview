# Module 3 Journal — PathReview Contribution

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `StructuralChunker.chunk()` method in `ingestion/chunking/structural_chunker.py` splits
documents by markdown headings to create RAG-ready chunks. When a document contains no
headings at all — such as a plain-text resume or a README with only prose — the method
returns an empty list instead of treating the full document as a single chunk. This means
heading-free documents are silently excluded from the vector index and will never be
retrieved during a review, producing incomplete feedback with no error or warning to signal
the data loss. The fix is to add a fallback at the end of `chunk()` that, when no sections
were extracted, wraps the entire document text in a single `Chunk` object and returns it.

**"Is this right for me?" checklist reasoning:**
- Scope: The change touches one method in one file (`structural_chunker.py`) plus the
  already-written test in `tests/unit/test_structural_chunker.py`. Total surface area is
  very small — well within a Tier 1 scope.
- Familiarity: The fix is pure Python with no external dependencies, no database work, and
  no API changes required.
- Reproducibility: The issue includes a three-line repro script and points to a specific
  failing test, so verifying the fix is straightforward.
- Risk: A fallback-only change can't regress documents that already have headings.
- Verdict: Good fit. Concrete problem, isolated fix, verifiable test already in place.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/nghiatra2006-jpg/pathreview/commit/10ed100f83aa69f9af826684c7d6b735bc8cc0d0

**Reproduction summary:**
Running `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings` fails with `assert 0 >= 1` — `chunk()` returns an empty list for a plain-text document because the guard in `_extract_sections()` discards all lines when `heading_stack` is empty, so no sections are ever built.

**PLAN.md link:** https://github.com/nghiatra2006-jpg/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** *(not recorded)*

**Blockers or open questions:**
Need to confirm before implementing that `strategy_selector.py` does not rely on an empty return from `chunk()` as a signal, and that `SemanticChunker` preserves `heading_path` metadata when sub-chunking the no-headings fallback section.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five PLAN.md sub-tasks complete. Implemented the no-headings fallback in
`StructuralChunker.chunk()` (15 lines added after `_extract_sections()` call). Added new
regression test `test_large_heading_free_document_is_sub_chunked` covering the >800-token
sub-chunking path. 16/16 unit tests pass, 0 regressions. Manually confirmed ruff introduces
0 new errors (4 pre-existing errors in unchanged code).

**Next steps:**
Push branch to GitHub, open draft PR against ascherj/pathreview, fill in PR template,
then mark ready for review.

**Blockers:**
GitHub auth requires a personal access token — need to set that up to push.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/353

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
Added a no-headings fallback in `StructuralChunker.chunk()`: when `_extract_sections()`
returns an empty list (because the document has no markdown headings), the full document
text is wrapped in a single synthetic section before the existing chunking loop runs.
Small heading-free documents (≤ 800 tokens) become one `Chunk`; large ones (> 800 tokens)
are handed off to `SemanticChunker` for sub-chunking — exactly the same path used for
large headed sections. Documents with headings are completely unaffected.

**Tests added or updated:**
- `tests/unit/test_structural_chunker.py` — existing `test_document_with_no_headings`
  now passes (was the failing test that reproduced the issue); new test
  `test_large_heading_free_document_is_sub_chunked` verifies that a 1,401-token
  heading-free document is sub-chunked into multiple `Chunk` objects and that caller
  metadata and `heading_level=0` are preserved through the sub-chunking path.

**Self-review confirmation:**
- [ ] make check passes — FAILS (pre-existing, not caused by this PR).
  `make lint`: ~100+ ruff errors across `agent/`, `api/`, `rag/`, `safety/`, `ingestion/`,
  and `tests/` — unsorted imports, unused variables, `Optional[X]` style, etc. — all in
  files not touched by this PR. Verified by running `make lint` with `.venv` set up.
  `make typecheck`: 5 mypy errors for missing stubs (`PyPDF2`, `jose`, `passlib`,
  `rank_bm25`, numpy) — all pre-existing, none in files changed by this PR.
  This PR introduces zero new lint or type errors.
- [x] make test-unit passes — 16/16 tests pass, 0 regressions
  (`make test-unit` with `.venv` set up confirms all pass)

**Draft PR feedback received from:** none
