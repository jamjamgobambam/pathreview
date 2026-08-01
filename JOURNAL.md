# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG evaluator's faithfulness checker decides whether a feedback claim is
backed by the retrieved context by counting how many meaningful (non-stopword)
words the claim and the context share, and it only counts a claim as "supported"
when that overlap is at least two words. Short but perfectly valid claims — like
"Knows Python." — carry only one content word, so even when the context fully
supports them they always fall below the threshold and are scored as unsupported.
As a result, feedback made up of short, well-grounded claims can score 0.0, and
three unit tests in `tests/unit/test_faithfulness_checker.py` fail. A successful
fix would let single-content-word claims be recognized as supported when that
word genuinely appears in the context, so faithfulness scores reflect real
grounding without newly rewarding unsupported claims. The bug lives in
`rag/evaluator/faithfulness_checker.py`, in the `_is_supported` helper.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this right for me?" — scope reasoning

- **Contained blast radius.** The defect is a single threshold in one helper
  (`_is_supported`) in one file. I can reason about the whole function without
  needing to understand the entire RAG pipeline.
- **Clear, reproducible failure.** The issue ships a minimal repro and names the
  exact failing tests, so I have an unambiguous definition of "done" (those tests
  pass) before I write any code.
- **Tier 1 fit.** As a first contribution to a large codebase, a well-specified
  single-function bug with existing test coverage is the right size — small
  enough to finish cleanly, real enough to exercise the full fork → branch →
  PR workflow.
- **Risk I'm watching:** the naive fix (drop the threshold to 1) could make the
  checker too lax and mark genuinely unsupported claims as supported. I'll need
  to keep the existing partial/varying-support tests green, not just the failing
  ones.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Adeola03/pathreview/commit/d0de22b

**Reproduction summary:**
Running the issue's exact snippet against the checker in a local venv returned
`0.0` for feedback whose claims are fully supported by the context, and the
three referenced unit tests fail for the same reason. I captured this in a new
failing test (`test_short_single_token_claims_are_supported_issue_152`) that
asserts a fully supported short claim must score above 0.0; it fails with
`assert 0.0 > 0.0`, pinning the bug to the `>= 2` overlap threshold in
`_is_supported`.

**PLAN.md link:** https://github.com/Adeola03/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** [not recorded yet]

**Blockers or open questions:**
Reproducing the bug surfaced that this is more than a one-line threshold change:
`test_partial_support_returns_middle_score` expects a *middle* score for a
single partially-grounded claim, which a binary supported/unsupported model
can't produce — so the fix needs graded per-claim scoring. The open question is
tuning that graded model (and the stop-word list) so a fully supported claim
still scores > 0.5 while a partially supported one lands in 0.2–0.8, without
letting unsupported claims score as supported. I'll validate the exact numbers
against the test suite in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix in `rag/evaluator/faithfulness_checker.py`. Worked
through all five PLAN.md sub-tasks: added punctuation-aware tokenization
(`[a-z0-9]+`) so `"Python,"` matches `"python"`; replaced the binary
`overlap >= 2` rule with a graded per-claim score `overlap / (overlap + 2)`;
averaged those scores in `check()`; lowered the claim length filter so short
claims like "Knows SQL" survive; and made `check()` tolerate `None`/missing
chunk text. All 23 tests in `tests/unit/test_faithfulness_checker.py` pass,
including the three the issue named and my #152 reproduction test.

**Next steps:**
Run the full `make check` / `make test-unit` to document pre-existing failures,
open a draft PR for peer feedback, then mark it ready.

**Blockers:**
None blocking. Noted that `main` already has repo-wide lint and unit-test
failures unrelated to this issue; confirming my change adds none.

---

### Check-in 2 (end of week)

**PR link:** <!-- PASTE your PR URL here after opening it, e.g. https://github.com/ascherj/pathreview/pull/NN -->

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
The faithfulness checker now grades each claim by how many meaningful tokens it
shares with the retrieved context (`overlap / (overlap + 2)`) instead of
requiring two or more shared tokens, so short single-term claims like
"Knows Python." are credited as supported and feedback of short grounded claims
no longer scores 0.0. Tokenization is punctuation-aware, short claims are kept,
and missing/`None` chunk text is handled gracefully.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added
`test_short_single_token_claims_are_supported_issue_152` (reproduction/regression
for the exact issue example) and gave the previously assertion-less
`test_common_words_filtered_in_overlap` a real assertion. The three tests named
in the issue plus `test_none_context_chunk_text` now pass; 23/23 in the file.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
<!--
"Passes" = introduces no NEW failures, per the assignment's pre-existing-failures
guidance. Verified with LLM_PROVIDER=mock:
  - Full unit suite: main = 53 failed / 375 passed; this branch = 49 failed / 380 passed.
  - Diff of failing-test sets: 0 new failures; this branch fixes the 4 faithfulness tests.
  - The 49 remaining failures are pre-existing and unrelated (test_resume_parser,
    test_review_service, test_security, test_skill_extractor, test_structural_chunker,
    test_tech_detector). `ruff check .` and `black --check .` also already fail on main
    repo-wide; the files changed here are ruff/black/mypy clean.
-->

**Draft PR feedback received from:** none <!-- replace with peer/mentor name or Slack handle if you get review -->

