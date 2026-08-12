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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer review has arrived on
[PR #771](https://github.com/ascherj/pathreview/pull/771) as of the end of Week 10.
The PR is open and marked ready for review with zero reviews submitted, no
reviewers assigned, and no review comments. The only pre-submission feedback I
received was the draft review from my cohort's tech fellows and my Week 9 breakout
room group, which I documented in Check-in 2 and acted on before submitting.

**How you responded:**
Nothing to respond to yet. If a maintainer does comment, the two things I already
flagged for them in Notes for Reviewers are where I expect it to land: the choice
of `heading_path=""` / `heading_level=0` as the metadata for a headingless chunk
(I offered a `"(no heading)"` alternative as a one-line change in `_build_section`),
and whether the supporting files — `PLAN.md`, `FAILING_TESTS.md`, `JOURNAL.md`, and
the `Makefile` `services` target — belong in the diff or should be stripped so the
PR touches only `ingestion/` and `tests/`. I'd make either change on request.

---

### Reflection

**What was harder than you expected?**
Getting the environment running, by a wide margin — I lost more time to setup than
to the actual bug. Docker Desktop failed on me, and my attempt to fix it by deleting
and reinstalling the app turned into its own problem, so I was stuck debugging a
container runtime instead of a chunker. I eventually switched to Colima
(`brew install colima docker docker-compose`, `colima start`, then
`docker compose up`), which suited me better anyway since I prefer working in the
terminal over running a desktop app, and because Colima provides the same daemon
socket `docker compose` talks to, `docker-compose.yml` worked unchanged. I hadn't
expected "get the app running locally" to be the hardest part of contributing to
someone else's project, but none of the issue work could start until it was solved.
A distant second was the pre-existing test noise: `make test-unit` on `main` returns
53 failures and `make check` returns 178 ruff errors, so before touching any code I
had to triage them into FAILING_TESTS.md — the largest cluster being 13 failures in
`test_review_service.py` from an `execute()` coroutine never being awaited in
`core/services/review_service.py`, none of it related to chunking.

**What did you learn about working in a large codebase?**
The cost of a change isn't the diff size, it's the blast radius, and you can't see
the blast radius from the file you're editing. My actual code change was small, but
the decision that took the longest was what metadata a headingless chunk should
carry: I had to grep every consumer of `heading_path` across `rag/` and the frontend
before I could be confident that an empty string wouldn't render as something broken
downstream. In my own projects I'd have just picked something and fixed the fallout
later. The other thing that surprised me is that a green test suite doesn't mean the
behavior is pinned — `test_heading_path_format` and `test_heading_path_breadcrumb`
both computed a `found_path` flag and then never asserted it, so they would have
passed even if `heading_path` had vanished entirely. I only noticed because I was
reading them to copy their patterns.

**How did AI tools help — and where did they fall short?**
AI was genuinely fast at the tracing work: pointing me at the three interlocking
conditions in `_extract_sections` that together caused the drop — the
`if heading_stack or current_section_lines` guard on the content branch, the
final-save requiring `current_section_lines and heading_stack`, and `heading_stack`
only ever being populated inside the `if heading_match:` branch — would have taken
me much longer alone. It was also good at drafting structure, like the PLAN.md
sections and the PR description skeleton. Where it fell short was judgment about
scope and conventions. It generated a `Makefile` change that wired `setup`, `run`,
`migrate`, and `test-all` to a Colima `services` target, which solved my local
problem but would hard-fail for any contributor who doesn't have Colima installed —
that's a change I had to recognize as scope creep on a chunking PR, and I still had
to disclose it rather than pretend it belonged. It also couldn't tell me whether
`PLAN.md` and `JOURNAL.md` should be in an upstream PR or whether to squash my
commits; both answers came from the tech fellows, who knew what this project's
maintainers actually want. Early on it also floated a `text.split("\n")` explanation
for the bug that I had to disprove by hand — a single line with no newline still
yields a one-element list, so the loop runs fine and the drop is entirely about the
missing heading match. I wrote that into PLAN.md specifically so I wouldn't
re-litigate it.

**What would you do differently if you started over?**
Two things. First, I'd capture the failing-test and lint baseline in Week 7 when I
picked the issue, not in Week 8 — I spent time second-guessing whether I'd broken
something before I had a baseline to compare against, and that anxiety was entirely
self-inflicted. Second, I'd keep the branch strictly scoped: the Colima `Makefile`
work was real and useful, but it belonged on its own branch or its own issue, not
committed alongside the #149 fix where it now sits in the diff needing a paragraph
of explanation. I'd also open the draft PR on Monday or Tuesday instead of near the
deadline — I got useful feedback from the tech fellows, but late enough that acting
on anything substantial would have been a scramble.

**What are you most proud of from this module?**
`test_whitespace_only_preamble_emits_no_empty_chunk`. The fix works by removing a
guard so content is always collected, and the failure mode that introduces is the
opposite of the original bug — the fallback firing when it shouldn't and emitting
empty chunks for blank preambles. Writing a test for the way my own fix could go
wrong, rather than only for the behavior the issue asked for, is the part of this
that felt like actual engineering instead of just making a red test green. The two
dead assertions I found in the existing tests are a close second, because they were
the moment I stopped reading the codebase as an authority and started reading it as
something written by people under deadline pressure, same as me.

