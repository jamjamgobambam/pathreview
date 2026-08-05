# Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [✓] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
There is a bug that occurs when the faithfulness checker receives a chunk of text, where the text is the key but the value is `None`. The broken behavior stems from `chunk.get("text", "")`​ because it only uses the empty string when the key is missing. However, if the key has the value `None`​, it returns `None`​ but later fails because `" ".join(...)` expects strings. A successful fix should result in the faithfulness checker being able to handle both missing and empty chunk text without crashing and continue with its evaluation.

**Branch name:** [fix/153-faithfulness-none-text]

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/ascherj/pathreview/commit/5b47b1e28e418f09d4f1f9c5c9a833feff0e1161]

**Reproduction summary:**
I created a script that called `FaithfulnessChecker().check()` with a context chunk that contained `{'text': None}`. This raised  `TypeError: sequence item 0: expected str instance, NoneType found`.

**PLAN.md link:** [https://github.com/Namisa-Mbayo/pathreview/blob/fix/153-faithfulness-none-text/Plan.md]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix in `rag/evaluator/faithfulness_checker.py`. The original code used `chunk.get("text", "")` and would raise errors against `None` values. I updated the context text extraction portion of the code so that `None` text values were treated as empty strings before joining.

*Subtasks Completed:*

- Inspect `faithfulness_checker.py` and find where the context chunks join to create the context string
- Update the context text extraction so that a chunk with `text: None` produces a valid string value, treating it as an empty string.
- Run `test_none_context_chunk_text` to confirm the bug is fixed.

**Next steps:**
I still need to verify is that the full unit test suite and project checks don't introduce new failures after implementing the fix.

**Blockers:**
No major blockers right now.

---

### Check-in 2 (end of week)

**PR link:** [https://github.com/ascherj/pathreview/pull/956]

**Branch:** `fix/153-faithfulness-none-text`

**What you built:**
I fixed the faithfulness checker so it doesn't crash when it receives a context chunk that has `"text": None`.

**Tests added or updated:**
[Which test files did you touch? What do they cover?]
I did not need to add a new test file because the faithfulness checker tests already cover this issue. I verified the fix using `test_faithfulness_checker.py`, specifically the `test_none_context_chunk_text` case, which checks that a context chunk with `text: None` doesn't raise a `TypeError`.

**Self-review confirmation:** [✓] make check passes  [✓] make test-unit passes

**Draft PR feedback received from:** None
