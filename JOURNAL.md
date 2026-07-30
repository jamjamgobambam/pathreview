# PathReview Contribution Journal

A running record of my Module 3 work on PathReview.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is in PathReview's StructuralChunker, which only creates sections from content that appears under Markdown headings. If a document contains no headings, _extract_sections never records any text, causing chunk() to return an empty list. As a result, heading-less documents are silently excluded from the RAG indexing pipeline and cannot be retrieved during searches. A successful fix would ensure that any non-empty document without headings is still chunked—either as a single chunk or by using the semantic chunker fallback—so every valid document contributes at least one chunk to the index and the existing test_document_with_no_headings passes.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

Issue Selection & Readiness
"Is this right for me?" — Scope reasoning (selection notes)
Single, well-defined location. The bug lives in one file, ingestion/chunking/structural_chunker.py (specifically the content-collection guard in _extract_sections). No cross-subsystem changes are required.
Clear, reproducible failure. Running StructuralChunker().chunk("plain text ...", {}) returns []. This is easy to reproduce and verify once fixed.
Existing test defines "done". There is already a failing unit test, test_document_with_no_headings in tests/unit/test_structural_chunker.py. The goal is to make that test pass without breaking the existing heading-based tests.
Right size for a first contribution. The issue is tagged Tier 1 and good first issue, making it a small, localized fix rather than a large refactor.
I understand the surrounding code. I traced the issue to the if heading_stack or current_section_lines guard in _extract_sections, which prevents content from being collected when a document has no headings.
Conclusion. This issue is within my current skill level and is an appropriate first open-source contribution.
Setup Notes
Forked the repository and cloned it locally.
Configured remotes:
origin → samanth1111-1111/pathreview
upstream → ascherj/pathreview
Created a .env file from .env.example using LLM_PROVIDER=mock.
Installed frontend dependencies with npm install.
Verified the Vite development server runs at http://localhost:5173.
Outstanding: Install Docker Desktop and make, then run make setup and make run to start PostgreSQL, Redis, and the backend services.
Part 1 — Understanding the Issue
Can I explain what this issue is asking for in my own words?

The issue occurs because the structural chunker only collects text after encountering a Markdown heading. If a document has no headings, it produces no chunks. The fix should ensure that plain-text documents are still chunked instead of being silently dropped.

✅ I can explain the problem and the expected behavior in 2–3 sentences without rereading the issue.
Do I understand which part of the app is affected?

The issue affects the ingestion pipeline, specifically the structural chunking logic in ingestion/chunking/structural_chunker.py.

✅ I've located the relevant files and confirmed they exist in the codebase.
Do I understand what "done" looks like?

Before the fix, documents without Markdown headings produce no chunks. After the fix, they should still produce at least one chunk while preserving the existing behavior for documents that do contain headings.

✅ I can describe a concrete before-and-after.
Part 2 — Tier Fit
Is the tier a realistic match for where I am right now?

 Picking a Tier 1 issue is appropriate. The change is localized, has clear acceptance criteria, and does not require understanding the entire system.

Part 3 — Codebase Readiness
Can I find the relevant code?
✅ I've found and read the specific code the issue references.
Do I understand the surrounding code well enough to change it safely?

I understand how _extract_sections processes documents and where the bug occurs, so I can outline the change before editing the code.

✅ I've read enough surrounding context that I can write a rough plan for the fix.
Have I read the relevant test file?
✅ I've found the test file (tests/unit/test_structural_chunker.py) and reviewed the existing tests.
Part 4 — Scope and Time
How many others are already working on this issue?
19
Is the scope realistic for Weeks 8–9?

This Tier 1 issue is expected to take approximately 3–6 hours. Based on its scope, I am confident I can complete it before the Week 9 deadline.

✅ I've estimated the time required and believe it is realistic.
Are there any blockers or dependencies?

I still need to install Docker Desktop and make to run the full backend. However, this does not block this issue because the fix is in ingestion/chunking/structural_chunker.py and can be tested using the existing unit test with pytest.

✅ I have identified the remaining setup steps, and they do not block this fix.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/samanth1111-1111/pathreview/commit/2f3cdd1b44ae6536a094612a7aa9f49af6e7d17c

**Reproduction summary:**
I created a local venv, installed the two dependencies needed (`tiktoken`, `pytest`), and ran the existing unit test `tests/unit/test_structural_chunker.py::test_document_with_no_headings`, which fails with `assert 0 >= 1`. I also confirmed it directly: `StructuralChunker().chunk("plain text ..." * 20, {})` returns `[]`. I traced the cause to two guards in `_extract_sections` that only collect/emit content when `heading_stack` is non-empty, so a heading-less document produces zero sections and is silently dropped from the RAG index; I marked both lines with inline `BUG (#149)` comments in the reproduction commit.

**PLAN.md link:** https://github.com/samanth1111-1111/pathreview/blob/fix/149-structural-chunker-no-headings/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
Need to confirm what the downstream ingestion/indexer expects in `Chunk.metadata` for a heading-less chunk (empty `heading_path` string vs. omitting the key). Also deciding whether to also capture pre-first-heading "preamble" content as part of this fix or defer it to keep the change tight.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Resolved the Week 8 open question first: the only downstream consumer of chunk
metadata (`ingestion/embeddings/batch_processor.py`) reads `source_id` and
`chunk_index` via `.get()` with defaults and never requires `heading_path` to be
non-empty, so an empty `heading_path` string / `heading_level = 0` on the
heading-less path is safe. Implemented the fix in
`ingestion/chunking/structural_chunker.py` (PLAN sub-tasks 1 & 2): rather than a
separate fallback branch in `chunk()`, I fixed the root cause in
`_extract_sections()` so accumulated content is always emitted as a level-0
section (empty heading path) whenever content exists — even with no headings, or
before the first heading. `chunk()`'s existing logic then handles it: short text
→ one chunk, long text (> 800 tokens) → semantic sub-chunking, reusing the
already-tested token-budget path. The acceptance test
`test_document_with_no_headings` now passes, and I added 4 more tests
(single short chunk, long-doc sub-chunking, source-metadata preservation,
preamble-not-dropped).

**Next steps:**
Open a draft PR and request peer feedback in Slack; fill in the PR template;
mark ready for review after addressing feedback; then complete Check-in 2 with
the PR link.

**Blockers:**
None. (The repo has substantial pre-existing `make check` / `make test-unit`
failures unrelated to this issue — see Check-in 2 — but they do not block this
change.)

---

### Check-in 2 (end of week)

**PR link:** _(to be added when the PR is opened)_

**Branch:** `fix/149-structural-chunker-no-headings`

**What you built:**
Fixed `StructuralChunker._extract_sections()` so content in a document with no
Markdown headings (or content appearing before the first heading) is emitted as
a level-0 section instead of being silently discarded. `chunk()` then chunks it
normally — one chunk for short text, semantic sub-chunking for text over the
800-token limit — with `heading_path=""` and `heading_level=0`. Heading-based
documents are unaffected. Guarantee: any document with non-empty `text.strip()`
now yields at least one chunk.

**Tests added or updated:**
`tests/unit/test_structural_chunker.py` — the existing acceptance test
`test_document_with_no_headings` now passes; added `test_short_no_heading_doc_
produces_single_level0_chunk`, `test_long_no_heading_doc_sub_chunked`,
`test_no_heading_doc_preserves_source_metadata`, and
`test_preamble_before_first_heading_not_dropped`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> "Passes" here means *no new failures introduced*, per the Week 9 pre-existing-
> failure guidance. Documented baselines (measured on this branch with dev
> extras installed, Python 3.13):
> - `make test-unit`: **53 failed / 375 passed** before my change →
>   **52 failed / 380 passed** after. My change flips the acceptance test
>   fail→pass and adds 4 passing tests; it introduces **zero** new failures.
>   All 52 remaining failures are pre-existing in unrelated modules
>   (`test_tech_detector`, `test_skill_extractor`, etc.).
> - `make check`: `ruff` reports 3 pre-existing `F841` unused-variable errors in
>   test methods I did not touch; `black --check` would reformat 52 files
>   repo-wide (a committed black-version drift), including
>   `structural_chunker.py` *before* my change — so I matched the file's existing
>   committed style rather than reformat unrelated code; `mypy` fails inside a
>   numpy stub (`Type statement is only supported in Python 3.12+`) before
>   reaching my file. None of these are caused by or affected by my change.

**Draft PR feedback received from:** _(to be added)_