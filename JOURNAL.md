## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker assumes every context chunk's `text` value is a
string. When the key exists but its value is `None`, the default supplied to
`dict.get()` is not used, so the null value reaches `" ".join(...)` and raises
a `TypeError`. A successful fix in `rag/evaluator/faithfulness_checker.py`
will normalize null chunk text safely and make the related unit test pass.

**Branch name:** fix/153-faithfulness-checker-crashes-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
