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

**PR link:** https://github.com/ascherj/pathreview/pull/292

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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was provided. This is expected for the
Summer 2026 course cycle, in which reviewer feedback is not available.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was separating a very small bug from the surrounding noise in
the repository. The failure came from one subtle Python behavior:
`chunk.get("text", "")` uses the default only when the key is missing, not when
the key exists with a value of `None`. Reproducing that exact path was simpler
than deciding how broad the fix should be. I had to avoid hiding unrelated bad
input by converting every value to a string, while still making null text safe.
It was also harder than expected to interpret repository-wide check failures
that were outside my change and distinguish them from the focused regression
tests that exercised issue #153.

**What did you learn about working in a large codebase?**
I learned that a correct change is not just code that stops the immediate
exception. In someone else's production code, I first needed to trace the
input shape into `FaithfulnessChecker.check()`, understand the existing scoring
behavior, and preserve that behavior for valid chunks. I kept the production
change to `chunk.get("text") or ""` and added both a null-only test and a mixed
null/valid test. The second test mattered because it showed that handling one
bad chunk did not discard useful context from the rest of the list. I also
learned to keep the issue, reproduction commit, plan, implementation, tests,
and PR connected so another contributor can follow why the change exists.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for navigating unfamiliar files, explaining the
`dict.get()` edge case, suggesting focused test cases, and helping format the
code and journal consistently. They accelerated the mechanical work, but they
could not decide the project's intended boundary for malformed inputs or tell
me whether unrelated full-suite failures were acceptable. I still had to read
the implementation and existing tests, reproduce the exception locally,
compare the proposed behavior with the issue, and judge that `None` should be
treated as empty text without broadly coercing every unexpected type.

**What would you do differently if you started over?**
I would run the focused failing test and the repository-wide checks immediately
after setup, before making any changes. That would create a clearer baseline
for which failures already existed and reduce uncertainty when `make check`
and `make test-unit` later reported failures outside my patch. I would also
write down the acceptance cases earlier—missing `text`, `text: None`, and a
mixture of null and valid chunks—so the implementation boundary was explicit
before coding. Finally, I would keep the PR link and check results updated in
the journal as each step happened instead of returning to documentation at the
end.

**What are you most proud of from this module?**
I am most proud of turning a one-line-looking crash into a precise regression
story. I reproduced the exact `TypeError`, explained why the existing default
did not work, made a narrow fix, and added a mixed-context test that protects
valid scoring behavior as well as preventing the crash. That gives a future
maintainer more confidence than a change that only makes the original test
stop failing.
