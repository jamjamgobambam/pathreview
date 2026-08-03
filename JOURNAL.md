## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The partial-overlap unit test in `tests/unit/test_relevance_scorer.py` uses a query and chunk that share every query term. Because the relevance scorer measures query-token coverage, it correctly returns `1.0`, contradicting the test's expectation of a middle-range score. The fixture needs to omit some query terms while retaining others so it represents genuine partial overlap. A successful fix makes the test exercise the intended behavior without changing the correct scoring implementation.

**Branch name:** test/157-partial-overlap-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/xyin20/pathreview/commit/fac1dda72ac9ca4ab6a91ec808d66f7de0f73129

**Reproduction summary:**
I restored the original all-four-term fixture and ran the focused relevance scorer tests. The scorer correctly returned `1.0`, producing `assert 1.0 < 0.9` and a result of `1 failed, 18 passed`.

**PLAN.md link:** https://github.com/xyin20/pathreview/blob/test/157-partial-overlap-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
None.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I completed all five sub-tasks from `PLAN.md`: retained the four-token query, revised the chunk to a genuine two-of-four-term overlap, confirmed the score is `0.5`, ran the focused scorer suite, and verified that no production scoring code changed. The focused `tests/unit/test_relevance_scorer.py` suite passes all 19 tests.

**Next steps:**
Run the repository-wide unit and contribution checks, compare any failures with `origin/main`, open a draft PR, and request feedback before final submission.

**Blockers:**
The repository has numerous pre-existing lint, formatting, type-checking, and unit-test failures outside the relevance scorer.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/694

**Branch:** `test/157-partial-overlap-fixture`

**What you built:**
I corrected the partial-overlap test fixture so the chunk matches only `Python` and `Django` from the four-term query. The unchanged scorer now returns the intended `0.5` coverage score instead of the correct-but-unexpected full-coverage score of `1.0`.

**Tests added or updated:**
Updated `tests/unit/test_relevance_scorer.py` so `test_query_with_partial_overlap` exercises genuine partial coverage. The focused file passes 19 tests; compared with `origin/main`, the full suite improves from 52 failures/345 passes/31 errors to 51 failures/346 passes/31 errors with no new failures.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Verification note:** Per the documented pre-existing-failure policy, the checked boxes mean this contribution introduces no new failures. GNU Make was unavailable on this Windows host, so I ran its exact underlying commands: Ruff reports 182 pre-existing errors, Black would reformat 52 pre-existing files, and mypy reports five pre-existing dependency/type errors. The full unit-suite baseline comparison confirms this branch removes issue #157's one failure and otherwise matches `origin/main`.

**Draft PR feedback received from:** none
