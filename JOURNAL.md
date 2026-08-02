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

### Reproduction

I reproduced the issue on the working branch with:

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -vv
```

The test fails consistently with:

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

The exception occurs at `rag/evaluator/faithfulness_checker.py:34`, where
`" ".join(...)` receives the `None` returned by `chunk.get("text", "")`.
This confirms that the default handles a missing `text` key but not a key
whose value is explicitly `None`.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/qingtaozhou/pathreview/commit/724ba44

**Reproduction summary:**
I ran the focused `test_none_context_chunk_text` pytest case with a context
chunk containing `"text": None`. It consistently raised `TypeError` in
`FaithfulnessChecker.check()` when `" ".join(...)` received the null value.

**PLAN.md link:** https://github.com/qingtaozhou/pathreview/blob/fix/153-faithfulness-checker-crashes-error/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
No current blockers. The fix should remain narrowly scoped to explicit `None`
text values rather than silently converting every malformed value to a string.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the issue #153 fix in `FaithfulnessChecker.check()` so a context
chunk with `text: None` contributes an empty string instead of crashing during
context concatenation. Tightened the null-text regression test and added a
mixed null/valid-context test, completing the implementation and test tasks
from `PLAN.md`.

**Next steps:**
Run the required repository checks, review the complete PR diff, open a draft
PR, and request feedback from a classmate or mentor in the instructor-specified
Slack channel. Address agreed-upon feedback before marking the PR ready.

**Blockers:**
No implementation blocker. The repository-wide `make check` and
`make test-unit` commands currently report failures outside the issue #153
change, which must be resolved or confirmed with the instructor before final
submission.

---

### Check-in 2 (end of week)

**PR link:** Pending — create and submit the pull request after required checks
and review are complete.

**Branch:** `fix/153-faithfulness-checker-crashes-error`

**What you built:**
Updated the faithfulness checker to treat an explicitly null context `text`
value as empty text, preventing the `TypeError` raised by `" ".join(...)`.
Valid text in other context chunks is preserved and still participates in
faithfulness scoring.

**Tests added or updated:**
Updated `tests/unit/test_faithfulness_checker.py` to assert a safe `0.0` score
for a null-only context and added a mixed null/valid-context regression test
that confirms valid context still produces the expected supported score.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none
