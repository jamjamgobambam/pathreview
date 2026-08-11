## Solution plan

**Issue:** #153 — TypeError in faithfulness_checker.py from unhandled None values
https://github.com/ascherj/pathreview/issues/153

### Understand

Expected: the faithfulness checker should score a claim (or mark it
unscorable) even when upstream data is incomplete. Actual: `dict.get()`
silently returns `None` for missing/null fields, and that `None` is passed
into logic expecting a concrete value, raising a `TypeError` instead of
failing gracefully.

### Map

- `rag/evaluator/faithfulness_checker.py` — primary fix location, the
  `.get()` call sites feeding unchecked values downstream.
- Any test file covering this evaluator (add/extend a regression test here).

### Plan

1. Identify every `.get()` call in the file whose result flows into an
   operation that assumes non-None (string ops, math, comparisons).
2. Add explicit None-handling: default values, early-return/skip logic, or
   an explicit "unscorable" result path — whichever matches the existing
   evaluator contract.
3. Add a regression test that feeds a claim with missing/None fields and
   asserts no exception + a defined, correct output.
4. Run the full evaluator test suite to confirm no regressions.
5. Update docstring/comments noting why the None-guard exists.

### Inputs & outputs

Input: a claim/result dict from the faithfulness pipeline, potentially
missing keys or containing None values. Output: a faithfulness score (or an
explicit "unscorable"/skip marker) — never an unhandled exception.

### Risks & unknowns

- Need to confirm what the _correct_ behavior is when a field is missing —
  score as 0, skip the claim, or raise a controlled/typed error instead of
  crashing? This affects downstream aggregation logic.
- Other callers of this function may depend on the current (crashing)
  behavior implicitly — need to check call sites before changing return
  shape.

### Edge cases

- All fields None.
- Only one field None, rest populated.
- Empty dict passed instead of None fields.
- Field present but wrong type (not None, but still invalid).
