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

