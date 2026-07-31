# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method builds its context string by pulling
`text` out of each chunk dict with `chunk.get("text", "")`, assuming that
missing keys are the only case it needs to guard against. But `.get()` only
falls back to the default when the key is absent — if a chunk explicitly has
`"text": None`, `.get()` returns `None`, and the subsequent `" ".join(...)`
call raises a `TypeError` because it can't join a `NoneType` into a string.
In practice this means any upstream chunk that legitimately has a null/empty
text field (rather than a missing one) crashes the faithfulness check instead
of being skipped or treated as empty. A correct fix should coerce `None`
values to an empty string (or filter the chunk out) before joining, so the
checker degrades gracefully instead of raising. This touches
`rag/evaluator/faithfulness_checker.py`, and there's already a failing test,
`test_none_context_chunk_text`, in `tests/unit/test_faithfulness_checker.py`
that should pass once the fix is in.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/adedotdev/pathreview/commit/966b683 (branch `fix/153-faithfulness-checker-none-text`)

**Reproduction summary:**
Ran the existing (failing) test `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`, which calls `FaithfulnessChecker.check()` with a chunk `{"text": None}`. It raised `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:39`, confirming `chunk.get("text", "")` returns `None` (not the default) when the key is present but explicitly `None`. Documented the reproduction with an inline comment at the crash site.

**PLAN.md link:** https://github.com/adedotdev/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** _not recorded yet_

**Blockers or open questions:**
The same `chunk.get("text", "")` pattern also exists in `review_generator.py`, `relevance_scorer.py`, and `hybrid.py` and likely has the same latent bug, but issue #153 only scopes the fix to `faithfulness_checker.py`. Also, 3 tests in `test_faithfulness_checker.py` fail today for reasons unrelated to this issue (claim-extraction/overlap-scoring logic) — need to confirm with a mentor whether that's separately tracked before I touch it in Week 9.
