## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [ X ] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The FaithfulnessChecker's `check()` method throws a TypeError whenever a context
chunk carries an explicit `text: None` value. The cause is a misuse of
`dict.get()`: its default (`""`) only applies when the key is missing entirely,
so a chunk like `{'text': None}` returns `None` rather than the intended empty
string. That `None` then flows into a `" ".join(...)` call, which requires every
element to be a string and raises `TypeError: sequence item 0: expected str
instance, NoneType found`. A successful fix makes the context-building step
defensive against present-but-null text — coercing `None` to `""` — so the
checker degrades gracefully instead of crashing. The change lives in
`rag/evaluator/faithfulness_checker.py`, verified by the existing
`test_none_context_chunk_text` test in `tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-none-chunk-text

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [paste link to your reproduction commit here]

**Reproduction summary:**
In an activated venv I ran `python -m pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v`
against the unmodified source and observed the test fail with
`TypeError: sequence item 0: expected str instance, NoneType found` raised at
`rag/evaluator/faithfulness_checker.py:34`, confirming the crash occurs inside
`check()` when a context chunk has `text: None`.

**PLAN.md link:** [paste link to PLAN.md on your branch here]

**Walkthrough video (recommended):** [paste Loom link here, or leave blank]

**Blockers or open questions:**
None — the root cause is confirmed and the fix approach is settled. The actual
one-line code change is scheduled for a later week per the module sequence.
