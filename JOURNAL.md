## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The faithfulness checker currently requires at least two meaningful overlapping words between a claim and the retrieved context before it marks the claim as supported. Because of this rule, short factual claims such as “Knows Python” are incorrectly scored as unsupported even when the context clearly mentions Python experience. The issue affects the claim-support logic in `rag/evaluator/faithfulness_checker.py`. A successful fix should allow short claims to be recognized from one meaningful keyword while still keeping stronger matching requirements for longer claims.

**Is this right for me? Selection notes:**

This issue is labeled Tier 1 and has a focused scope in one main component of the codebase. The issue description includes a clear example, identifies the relevant file, and lists related tests, so I can reproduce the problem and verify the fix. The work involves Python, string processing, and unit testing, which are skills I am comfortable using. I also confirmed that the issue was open and not assigned before claiming it.

**Branch name:** `fix/152-short-claim-support`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 – Reproduction & solution planning

**Reproduction commit link:**
[\[link\]](https://github.com/winniehappi1/pathreview/blob/fix/152-short-claim-support/JOURNAL.md)

**Reproduction summary:**

I reproduced Issue #152 by running the faithfulness checker unit tests locally using pytest. The tests showed that short supported claims were incorrectly scored as unsupported, and a None value in a context chunk caused a TypeError.

**PLAN.md link:**
[\[link\]](https://github.com/winniehappi1/pathreview/blob/fix/152-short-claim-support/PLAN.md)

**Walkthrough video:**
Not recorded.

**Blockers or open questions:**
None at this time.