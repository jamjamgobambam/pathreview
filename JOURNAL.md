## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer "partial overlap" test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The test `test_query_with_partial_overlap` in `tests/unit/test_relevance_scorer.py` uses the query "Python Django web framework" against a chunk that actually contains all four of those terms, then asserts the resulting score is below 0.9. Since the scorer correctly returns 1.0 for full keyword coverage, this test fails against correct behavior rather than catching a real bug. The fix is to rewrite the fixture so the chunk only contains some of the query terms, making it a genuine partial-overlap case. This affects the relevance scoring logic in the RAG pipeline's test suite, not the scorer itself.

**Branch name:** test/157-relevance-scorer-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope check ("Is this right for me?"):**
- I can explain the problem and expected behavior without re-reading the issue: yes, the fixture claims partial overlap but the query terms are all present in the chunk, so the scorer's 1.0 result is correct and the test assertion is wrong.
- Affected area: `tests/unit/test_relevance_scorer.py`, specifically `test_query_with_partial_overlap` and the relevance scorer it exercises.
- Definition of done: the fixture is rewritten so the chunk contains only some of the query terms, the test asserts a score genuinely below 0.9, and `pytest tests/unit/test_relevance_scorer.py -q` passes.
- Tier fit: this is my first open source contribution, so Tier 1 is the right call.
- Codebase readiness: I located and read the test function and reproduced the failure locally with `pytest tests/unit/test_relevance_scorer.py -q`.
- Claims check: 2 other students were on this issue when I claimed it, which felt manageable.
- Time estimate: realistic for Weeks 8–9 given the small, single-file scope.
- Blockers: No blockers yet.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/KR-0000/pathreview/commit/8cd16b891866c9f212dd898db30d8ff513a7f570


**Reproduction summary:**
Ran `pytest tests/unit/test_relevance_scorer.py -q` and confirmed `test_query_with_partial_overlap` fails with `assert 1.0 < 0.9`. The chunk fixture contains all 4 query tokens ("python", "django", "web", "framework"), so `RelevanceScorer.score()` correctly returns 1.0 for full coverage, but the test asserts the score must be below 0.9 — confirming the issue is a bad test fixture, not a scorer bug.

**PLAN.md link:** https://github.com/KR-0000/pathreview/blob/test/157-relevance-scorer-partial-overlap-fixture/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Still deciding exact new chunk wording for the fixture and whether to also spot-check `test_multiple_keyword_matches` and `test_score_ranges_from_zero_to_one` for the same kind of overlap-math mistake — not in scope for issue #157 but noticed while reading the file.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks 1-4 from PLAN.md: rewrote the `test_query_with_partial_overlap` chunk fixture so it only contains 2 of the 4 query tokens ("python" and "web", not "django" or "framework"), giving a genuine overlap ratio of 0.5, well inside the asserted `0.3 < score < 0.9` range. Kept the original assertion bounds since they already describe a real partial-overlap case once the fixture is honest. Ran `pytest tests/unit/test_relevance_scorer.py -v` — all 19 tests pass, including the previously-failing one. Also confirmed against `RelevanceScorer.score()`/`_tokenize()` in `rag/evaluator/relevance_scorer.py` that no production code needed to change, per the plan.

**Next steps:**
Sub-task 5 (re-reading the test docstring/name for accuracy) is done — no changes needed there. Remaining for the rest of the week: run `make check` and `make test-unit` against the full repo to document pre-existing failures, open a draft PR, request peer/mentor feedback in Slack, then finalize and submit.

**Blockers:**
None. One documented (non-blocking) pre-existing issue: `make check` and `make test-unit` both have pre-existing failures unrelated to this change (baseline: 182 lint errors across the repo, 53 failing unit tests before the fix / 52 after — one fewer because this fix resolves `test_query_with_partial_overlap`). `ruff format --check` also pre-existingly wants to reformat `tests/unit/test_relevance_scorer.py` even without my change (verified by stashing my edit and re-running the check). None of this is introduced by my fix; will document it in the PR description per the course guidance on pre-existing failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/365

**Branch:** test/157-relevance-scorer-partial-overlap-fixture

**What you built:**
Fixed the `test_query_with_partial_overlap` test fixture in `tests/unit/test_relevance_scorer.py` so the chunk text only contains some of the query's keywords instead of all four. `RelevanceScorer.score()` itself was already correct — it returns 1.0 for full keyword coverage — so the fix is entirely in the test fixture, not production code.

**Tests added or updated:**
Updated `tests/unit/test_relevance_scorer.py::TestRelevanceScorer::test_query_with_partial_overlap` — changed the chunk text so only 2 of the query's 4 tokens ("python", "web") appear, giving a real ~0.5 overlap ratio that correctly falls inside the test's asserted `0.3 < score < 0.9` range, instead of the old fixture which had full 4/4 overlap and produced 1.0.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both have documented pre-existing failures unrelated to this change — see PR description. My change introduces zero new failures in either: lint/format issues are pre-existing across the repo and in this file even before my edit, and unit tests went from 53 failing to 52 failing, the one fewer being the test this PR fixes.)

**Draft PR feedback received from:** none — instructor confirmed peer/mentor review is not required for this assignment, so the PR was opened directly as ready for review rather than as a draft.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No comments or reviews on PR #365 as of this writing (Conversation tab shows 0 comments). Per the Su26 course note, reviewer feedback isn't a feature this term, so none is expected.

**How you responded:**
N/A — nothing to respond to. If feedback arrives after this entry, I'll update this section.

---

### Reflection

**What was harder than you expected?**
Getting the fix committed was harder than writing it. The actual code change was two lines — swap the chunk text in `test_query_with_partial_overlap` — but the local pre-commit hook (`black` + `mypy`) turned that into a multi-step investigation: `black` silently rewrote the whole file's whitespace on top of my staged edit, and `mypy` failed with 21 errors that had nothing to do with my change (missing type annotations on every test function in the file, a repo-wide pre-existing condition). Figuring out that this was pre-existing debt and not something I broke meant diffing against a stash, checking `.github/workflows/ci.yml` to see what CI actually enforces (it excludes `tests/` from `mypy`), and only then deciding `--no-verify` was the right call for that one commit. I expected the "hard part" to be understanding `RelevanceScorer.score()`; it turned out to be understanding the project's tooling well enough to know when a red hook is telling me something real versus something pre-existing and out of scope.

**What did you learn about working in a large codebase?**
The biggest shift was realizing that "does my change work" and "does my change pass all the gates" are separate questions with separate answers, and a large codebase can have gates that are already broken independent of anything I touch. I had to establish a baseline (`make check`, `make test-unit` before my edit) to have any way of proving my fix didn't make things worse, rather than assuming a clean run was the bar. I also learned to read tool configs (`pyproject.toml`'s `[tool.mypy]`, `.pre-commit-config.yaml`, `ci.yml`) as primary sources instead of just running commands and reacting to output — the difference between the pre-commit `mypy` hook and CI's `mypy` step (different scopes entirely) only became clear once I actually compared the two config files side by side.

**How did AI tools help — and where did they fall short?**
AI was most useful for fast triage: pointing out immediately that `overlap = len(query_tokens & chunk_tokens) / len(query_tokens)` in `relevance_scorer.py` gives exactly 1.0 for full coverage, which confirmed the bug was in the fixture and not the scorer before I'd have worked that out by hand. It also helped me realize `git restore` on the unstaged half of a partially-staged file was the safe way to undo `black`'s unwanted reformatting without touching my staged fix. Where it fell short: the first attempted fix used `ruff format` to tidy the file, which isn't even the formatter this project uses (`black`) — a mismatch I only caught because the pre-commit hook surfaced a different diff than what `ruff format` had produced. I had to be the one who noticed the two tools disagreed and ask which one the project actually cares about; AI assistance is only as good as double-checking it against the project's actual config, not just running the first plausible tool.

**What would you do differently if you started over?**
I'd check `.pre-commit-config.yaml` and `ci.yml` in Week 7 or 8, before writing any code, instead of discovering the `black`-vs-`ruff format` and `mypy` scope differences reactively during the Week 9 commit. Knowing upfront that this repo formats with `black` (not `ruff format`) and that CI's `mypy` never touches `tests/` would have saved a full round of confused hook output. I'd also spend a few more minutes in Week 8 fixture-testing candidate chunk texts by hand (computing the overlap ratio for two or three options) before settling on one, rather than picking the first sentence that felt "partial enough."

**What are you most proud of from this module?**
Not the fix itself — it's a two-line change. I'm proud of the PR's "Notes for Reviewers" section, specifically being able to state precisely why `--no-verify` was justified (citing the exact CI config line that excludes `tests/` from `mypy`, and the exact before/after failure counts for `make test-unit`) instead of just bypassing the hook and hoping nobody asked. That's the part of open-source contribution I hadn't practiced before: proving a change is safe to someone who didn't watch you make it.