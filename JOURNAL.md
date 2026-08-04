## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/157

**Issue title:** Relevance scorer “partial overlap” test fixture actually has full query overlap

**Tier:** [x] Tier 1

**Problem summary:**
The relevance scorer test says it checks partial overlap, but its query matches every keyword in the text.
The scorer returns 1.0, so the assertion expects the wrong result.
The fixture should omit some query terms so the test checks partial overlap.

**Scope notes:** I read `tests/unit/test_relevance_scorer.py` and `rag/evaluator/relevance_scorer.py`.
This Tier 1 change is one fixture, the test is the finish condition, I estimate three hours, and no blocker is listed.
The current ledger allows duplicate claims.

**Branch name:** `test/157-partial-overlap-fixture`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DDDIGHE/pathreview/commit/d6f1ee5956b51c9d0c988f67655651cdc259174d

**Reproduction summary:** `pytest tests/unit/test_relevance_scorer.py -q` fails with `assert 1.0 < 0.9` because the fixture contains all four query terms.

**PLAN.md link:** https://github.com/DDDIGHE/pathreview/blob/test/157-partial-overlap-fixture/PLAN.md

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Reproduced issue #157 and completed the implementation plan.

**Next steps:** Update the partial-overlap fixture, run the relevant tests, and open the pull request.

**Blockers:** None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/766

**What you built:** Updated the partial-overlap fixture so it omits one query term and exercises the intended 0.75 relevance score instead of an exact match.

**Tests added or updated:** Updated `tests/unit/test_relevance_scorer.py`; all 19 relevance-scorer tests pass.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none

**Repository-wide check note:** `make check` reports 182 lint errors across the repository. `make test-unit` reports 376 passed and 52 failures outside the changed relevance-scorer test.
