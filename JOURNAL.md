## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: `None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker currently assumes every context chunk has a string in
its `text` field, but one valid edge case is `text: None`. In
`rag.evaluator.faithfulness_checker`, the code uses `chunk.get("text", "")`,
which still returns `None` when the key exists, and that causes `" ".join(...)`
to crash with a `TypeError`. This breaks faithfulness evaluation for otherwise
valid inputs and can fail test coverage in `test_none_context_chunk_text`.
A successful fix should sanitize chunk text values so missing or `None` values
are treated as empty strings and `check()` can continue safely.

**Branch name:** fix/faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" checklist:**
- [x] I can explain this issue in my own words and define what success looks like.
- [x] I identified the affected area (`rag.evaluator.faithfulness_checker`) and the related unit test (`test_none_context_chunk_text`).
- [x] Tier acknowledged: this is a Tier 1 issue, which matches my current comfort level because the fix is localized and low-risk.
- [x] Scope-fit reasoning: this issue is a good fit because it is a focused bug fix (handling `None` safely in chunk text processing) that should be solvable in one code path with supporting test coverage.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jess4342/pathreview/commit/c857ad603c037d3a6c84e4a1206af359dfa8d754

**Reproduction summary:**
I reproduced the issue with:
`C:/Users/jess/Documents/codepathAI2026/pathreview/.venv/Scripts/python.exe -m pytest tests/unit/test_faithfulness_checker.py -k none_context_chunk_text -q`.
The test fails with `TypeError: sequence item 0: expected str instance, NoneType found` in `rag/evaluator/faithfulness_checker.py` when `check()` builds `context_text` using `" ".join(...)` and a chunk contains `{"text": None}`.

**PLAN.md link:** https://github.com/jess4342/pathreview/blob/fix/faithfulness-checker-none-text/PLAN.md

**Blockers or open questions:**
Need to decide whether to sanitize only `None` values or all non-string `text` values (e.g., numbers, lists) to keep this code path robust.