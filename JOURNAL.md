# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness check

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue addresses an edge case in the faithfulness checker when a context chunk contains `{"text": None}`. The current implementation uses the chunk’s `text` value when building the combined context, but `None` is not a string and causes `join()` to raise a `TypeError`. A successful fix will normalize `None` text values into a safe string value while preserving existing behavior for valid context chunks.

**Branch name:** feat/153-faithfulness-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[link to commit documenting the reproduced issue\]](https://github.com/mxdmichael1-code/pathreview/commit/08975d3)

**Reproduction summary:**
I reproduced Issue #153 by running `TestFaithfulnessChecker::test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py`. The test fails because `FaithfulnessChecker.check()` passes a `None` value from a context chunk into `join()`, causing a TypeError instead of handling the missing text gracefully.

**PLAN.md link:** [\[link to PLAN.md in your fork\]](https://github.com/mxdmichael1-code/pathreview/blob/feat/153-faithfulness-check/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Not at the moment.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #153 by safely handling context chunks where `"text"` is `None` in `FaithfulnessChecker`. Verified that the new regression test passes. Confirmed that three existing failures in `test_faithfulness_checker.py` are pre-existing and unrelated to this change.

**Next steps:**
Run `make test-unit` and `make check`, review the final code changes, commit the implementation, open a draft PR, and request peer or mentor feedback.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** None

**Branch:** `feat/153-faithfulness-check`

**What you built:**
Implemented a fix for Issue #153 so that `FaithfulnessChecker` no longer raises a `TypeError` when a context chunk contains `"text": None`. The implementation safely treats `None` as an empty string while preserving the existing behavior for valid context chunks.

**Tests added or updated:**
Verified that the existing regression test for context chunks containing `"text": None` passes after implementing the fix. Also confirmed that the remaining failing tests are pre-existing and unrelated to this change.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** None