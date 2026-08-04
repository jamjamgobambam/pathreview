## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

Choosing Tier-1 since this is my first open-source contribution. Potential second issue after this is implemented: https://github.com/ascherj/pathreview/issues/44

**Problem summary:**
The structural chunker splits documents into sections using headings as
boundaries. When a document contains no headings, the chunker silently
drops it instead of falling back to a sensible default — such as treating the entire document as a single chunk. This means valid documents with no heading structure are never processed or stored, with no error or warning surfaced to the caller. A successful fix would add a fallback so heading-free documents are chunked as a whole unit rather than discarded silently.

We have a failing test `test_document_with_no_headings` in `tests/unit/test_structural_chunker.py.`. Once the correct fix is applied, it can be verified with this existing test.

**Branch name:** fix/149-structural-chunker-drops-headingless-docs

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Wodehouse/pathreview/commit/2d95f3d909cdc86cc98132c44708ebbc5aec6a63

**Local setup:**
To run the app locally I needed a container runtime. I used Colima instead of
Docker Desktop so everything runs from the terminal with no extra desktop app:
`brew install colima docker docker-compose`, `colima start`, then
`docker compose up` (frontend at localhost:5173). Colima provides the Docker
daemon/socket that `docker compose` talks to, so `docker-compose.yml` works
unchanged.

**Reproduction summary:**
Ran `make test-unit` and confirmed `test_document_with_no_headings` in
`tests/unit/test_structural_chunker.py` fails with `assert 0 >= 1` — a headingless
document produces 0 chunks. Traced it to `StructuralChunker._extract_sections`,
where a section is only ever created after a heading match, so a doc with no
heading has all its content discarded and returns `[]`. Full list of expected
pass/fail tests is captured in FAILING_TESTS.md.

**PLAN.md link:** https://github.com/Wodehouse/pathreview/blob/fix/149-structural-chunker-drops-headingless-docs/PLAN.md

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `ingestion/chunking/structural_chunker.py`; all four
PLAN.md sub-tasks are done. `_extract_sections` now collects content lines
unconditionally (sub-task 1), and a new `_build_section` helper emits a
headingless section with an empty path and level 0 when no heading has been seen
(sub-task 2). Verified `chunk()` routes the empty `heading_path` through both the
single-chunk and semantic sub-chunk branches (sub-task 3), and grepped
`heading_path` consumers to confirm nothing reads it except the chunker itself
(sub-task 4). Added 4 edge-case tests in `tests/unit/test_structural_chunker.py`;
the existing `test_document_with_no_headings` now passes (19/19 chunker tests
green). Committed as `fix(ingestion): …` + `test(ingestion): …`.

**Next steps:**
Open a draft PR and request peer/mentor review in Slack, address feedback, then
do a final `make check` / `make test-unit` pass and mark the PR ready for review
with Check-in 2.

**Blockers:**
None. The repo has documented pre-existing test/lint failures unrelated to this
change (tracked in FAILING_TESTS.md); the fix introduces no new failures
(unit suite goes 53 → 52 pre-existing failures, +4 new passing tests).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/771

**Branch:** `fix/149-structural-chunker-drops-headingless-docs`

**What you built:**
Fixed `StructuralChunker` silently dropping documents that contain no markdown
headings. `_extract_sections` previously only created a section as a side effect
of matching a heading, so a headingless document had every content line discarded
and returned zero chunks; it now collects content unconditionally and a new
`_build_section` helper emits a headingless section (empty `path`, `level` 0) when
no heading has been seen. Heading-free documents and pre-heading preambles are now
chunked as their own units — one chunk, or semantic sub-chunks past the 800-token
`SECTION_TOKEN_LIMIT` — while documents with headings chunk exactly as before.

**Tests added or updated:**
`tests/unit/test_structural_chunker.py` (the only test file touched). The
pre-existing `test_document_with_no_headings`, which was failing on `main` with
`assert 0 >= 1`, now passes. Added four edge-case tests:

- `test_headingless_doc_over_token_limit` — a headingless document larger than
  `SECTION_TOKEN_LIMIT` (800 tokens) routes through the semantic chunker and
  yields multiple non-empty chunks, confirming the fix isn't limited to short docs.
- `test_preamble_before_first_heading_preserved` — content before the first heading
  survives as its own chunk with `heading_path == ""`, *and* the following heading
  section is still emitted with `heading_path == "First Heading"`, so the preamble
  is not mis-attributed to the first heading.
- `test_whitespace_only_preamble_emits_no_empty_chunk` — a whitespace-only preamble
  is dropped rather than emitted as an empty chunk, guarding against the new
  fallback over-firing now that content collection is unconditional.
- `test_single_heading_no_body` — a lone heading line with no body neither crashes
  nor produces an empty-text chunk.

Also completed two pre-existing tests, `test_heading_path_format` and
`test_heading_path_breadcrumb`, which computed a `found_path` / `found_full_path`
flag but never asserted it — they would have passed even if `heading_path` had
disappeared entirely. Full file: 19 passed.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both boxes reflect the pre-existing-failure standard documented in
FAILING_TESTS.md: `main` already fails 53 unit tests and reports repo-wide
`ruff`/`mypy` errors in modules unrelated to issue #149. After my changes the unit
suite is 52 failed / 380 passed — no test that passed on `main` fails on this
branch — and the two files I touched are clean in isolation (`ruff check` passes,
`black --check` reports both unchanged, and `structural_chunker.py` itself is
`mypy`-clean; the 4 remaining `mypy` errors are inside the imported
`semantic_chunker.py` and are present on `main`).

**Draft PR feedback received from:** Cohort tech fellows and my Week 9 breakout
room group. They reviewed the draft PR description and advised (1) keeping the
supporting files — `PLAN.md`, `FAILING_TESTS.md`, `JOURNAL.md` — in the PR since
the plan is part of why the code changes happened, rather than stripping them out,
and (2) that CONTRIBUTING.md's "squash fixup commits" guidance applies to
superficial/debugging commits, not to real work commits, so my three conventional
commits should stay separate. Both points are reflected in the submitted PR.

