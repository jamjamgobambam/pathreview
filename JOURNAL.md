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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback arrived on [PR #883](https://github.com/ascherj/pathreview/pull/883) by the end of the module. Checked the PR directly — no reviews, no assigned reviewers, no comments. Per the Su26 course note, reviewer feedback isn't a wired-up feature this term, so this was expected rather than a sign the PR was overlooked.

**How you responded:**
N/A — nothing to respond to. I re-read my own PR description once more as a stand-in for review, looking for anything a reviewer would likely flag, and didn't find changes I'd make.

---

### Reflection

**What was harder than you expected?**
The fix itself (collect content lines unconditionally, always flush the trailing section) was a one-line-of-reasoning change once I'd read `_extract_sections()` closely — the hard part was proving it was *safe*, not writing it. My first pass introduced a subtler bug than the one I was fixing: making content collection unconditional meant leading blank lines before a document's first heading got appended to `current_section_lines`, and when the next heading hit, the code would flush a section whose content was just whitespace — an empty-text chunk, silently, which is exactly the failure mode I was supposed to be eliminating. I only caught it by mentally tracing a document that starts with blank lines before a heading, not from a failing test, since no existing test covered that shape. That was a good lesson: passing tests confirm the cases you thought of, not the cases you didn't. The other harder-than-expected part was environment drift — the venv was missing several dependencies pyproject.toml declared (`redis`, `structlog`, `pypdf`, `python-jose`), and `mypy` was broken repo-wide by a numpy/Python 3.14 stub incompatibility that had nothing to do with my change. Distinguishing "my change broke this" from "this was already broken" ate more time than the fix did, and required actually stashing my diff and re-running checks against a clean `main` to get a trustworthy answer instead of guessing.

**What did you learn about working in a large codebase?**
The instinct to just make the tests pass isn't enough — I had to go find out *who else* depends on the thing I'm changing before I could trust my fix. Before deciding that an empty string was an acceptable `heading_path` for heading-less chunks, I grepped `rag/` and `api/` for `heading_path` consumers, because a chunking-layer decision that looks purely local can quietly break a citation-rendering feature three layers away that I'd never think to test. In my own projects I've never had to ask "what does downstream code assume about this field," because I am the downstream code. I also learned to separate "is this broken because of me" from "is this broken already" as a discipline, not a one-off check — `git stash` + rerun became a reflex by the end of the week, not something I did once and trusted forever.

**How did AI tools help — and where did they fall short?**
Claude Code was most useful for the mechanical, verifiable parts of the loop: reading the existing test file conventions before writing new ones, running the suite repeatedly and summarizing 52 unrelated failures into "these are pre-existing, here's the stash-diff proof," and drafting a PR description dense enough that I could tell at a glance if it was actually substantive versus templated filler. It fell short at exactly the boundary of the environment: there's no `gh` CLI installed on this machine and no GitHub token available, so the AI could push my branch but could not open the PR itself — I had to open the compare link and paste the description in by hand. That's a fair division of labor in retrospect: the AI could get me to a fully-drafted, fully-tested PR, but the last step that actually makes something visible to a maintainer had to be a deliberate action I took, not one automated away for me.

**What would you do differently if you started over?**
I'd install and verify the full dev dependency set (`pip install -e ".[dev]"`) in Week 7 or 8, before writing any reproduction tests, instead of discovering the gaps in Week 9 while trying to get a clean test baseline. That would have separated "environment setup" from "solution building" instead of letting them collide in the same week. I'd also add the leading-blank-line-before-heading case to my reproduction tests during the Week 8 planning pass, since it's a direct corollary of the bug I was already documenting (preamble loss) — I got lucky that I caught it by inspection rather than by a test that would have caught it for me.

**What are you most proud of from this module?**
Catching my own regression before it shipped. It would have been very easy to see "18/18 tests pass" after the fix and call it done — the empty-chunk-on-leading-blank-lines bug wasn't caught by any test I inherited or any test I'd already written, only by re-reading my own change skeptically and asking what input would break it. That's the habit I most want to carry into the next module.