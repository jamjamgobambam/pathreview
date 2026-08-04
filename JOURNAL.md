## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker verifies that generated claims are actually supported
by the retrieved context, but it crashes when a context chunk has `None` as
its text value instead of an empty string. The code uses
`chunk.get("text", "")` to build the combined context string, which only
falls back to the default when the "text" key is missing entirely — if the
key exists but is explicitly `None`, `.get()` returns `None`, and joining a
list containing `None` with a string raises a TypeError. This affects the
`rag` module's faithfulness-scoring logic, and the fix would involve safely
coercing a `None` text value to an empty string before concatenation.

**Branch name:** fix/153-faithfulness-checker-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger 



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ReevaSharma/pathreview/commit/3f8f6c0

**Reproduction summary:** Ran `FaithfulnessChecker().check('Knows Python.',
[{'text': None}])` locally and confirmed it raises `TypeError: sequence
item 0: expected str instance, NoneType found`, matching the issue. Also
confirmed `test_none_context_chunk_text` in the existing test suite
currently fails with the same error.

**PLAN.md link:** https://github.com/ReevaSharma/pathreview/blob/fix/153-faithfulness-checker-none-text-crash/PLAN.md

**Blockers or open questions:**
None currently — the fix is a small, well-scoped one-line change.



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented the fix in `faithfulness_checker.py` —
changed `chunk.get("text", "")` to `chunk.get("text") or ""` so that a
`None` value is treated the same as a missing key. Confirmed the
previously-failing `test_none_context_chunk_text` now passes, and
`make test-unit` shows 52 failed / 376 passed (down from the 53/375
baseline), confirming no new regressions were introduced.

**Next steps:** Run `make check` to confirm no new lint issues in the
touched file, self-review against CONTRIBUTING.md, open a draft PR for
feedback, then finalize the PR description and submit.

**Blockers:** None.

