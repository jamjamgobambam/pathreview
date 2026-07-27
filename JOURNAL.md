# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The faithfulness checker builds a combined context string from the text stored in each retrieved context chunk. The current implementation provides an empty-string default only when the `text` key is missing, but it does not handle cases where the key exists and its value is `None`. As a result, the checker attempts to join a `None` value into a string and raises a `TypeError`. A successful fix will normalize `None` values to empty strings so that malformed or incomplete context chunks do not crash the faithfulness evaluation process.

**Selection notes:**

This issue is appropriately scoped because the failure has a clear reproduction case, identifies the affected faithfulness checker, and points to a related unit test. It is limited to safely handling one edge case rather than redesigning the RAG evaluation system. I can reproduce the failure locally, make a targeted change, and validate the behavior using unit tests. The issue is labeled Tier 1 and good first issue, making it suitable for my first contribution to this codebase.

**Branch name:** `fix/153-handle-none-context-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/anshbabar/pathreview/commit/006281741aac908beaae313e34f204f5adc06e31

**Reproduction summary:**

I reproduced the issue by running the existing `test_none_context_chunk_text` unit test with a context chunk containing `{"text": None}`. The test failed because `FaithfulnessChecker.check()` attempted to join a `None` value into a string, resulting in `TypeError: sequence item 0: expected str instance, NoneType found`.

**PLAN.md link:** https://github.com/anshbabar/pathreview/blob/fix/153-handle-none-context-text/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**

The issue is clearly reproduced, and the intended fix appears to be narrowly scoped. One open question is whether unexpected non-string values other than `None` should also be normalized, but that may be outside the scope of Issue #153.

### Baseline Test Comparison

The targeted regression tests for Issue #153 pass.

The full unit suite does not currently pass on either the project baseline or
this feature branch:

- Upstream `main`: 53 failed, 375 passed
- Feature branch: 52 failed, 377 passed

The feature branch contains one additional regression test. It also fixes the
existing `test_none_context_chunk_text` failure, so the branch has one fewer
failure and two additional passing tests overall. The implementation therefore
introduces no new unit-test failures relative to upstream `main`.

The repository-wide quality check also reports errors in unrelated files.
- Mypy reports pre-existing file-wide annotation errors in `tests/unit/test_faithfulness_checker.py`; this contribution does not claim a repository-wide mypy pass.
this contribution.


## Week 9 — Implementation & PR

### Check-in 1 — Implementation progress

**Current progress:**

- Updated `FaithfulnessChecker.check()` to safely handle context chunks containing `text: None`.
- Added regression coverage for the reported crash.
- Verified that valid context remains usable when another chunk contains `None`.

**Next steps:**

- Complete the final code review.
- Push the implementation and tests.
- Update the pull request description.

**Blockers:**

The complete repository test suite contains unrelated baseline failures. The Issue #153 targeted tests pass.


### Check-in 2 — Final submission

**PR link:** https://github.com/ascherj/pathreview/pull/741

**Branch:** `fix/153-handle-none-context-text`

**What I built:**

Updated the faithfulness checker so that context chunks containing `text: None`
are normalized to empty strings instead of causing `" ".join(...)` to raise a
`TypeError`. Valid context from other chunks is preserved.

**Tests created or modified:**

- Confirmed a chunk containing `{"text": None}` does not crash.
- Confirmed a missing `text` key does not crash.
- Added coverage for mixed valid and `None` context chunks.

**Self-review:**

- [ ] `make check` passes repository-wide
- [ ] `make test-unit` passes repository-wide

The repository-wide commands remain unchecked because the project baseline has
unrelated failures.
