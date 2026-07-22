## Week 7 — Issue selection

**Issue link:** [paste GitHub issue URL here]

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
