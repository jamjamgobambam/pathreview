## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

This is my first time resolving a bug in a large codebase, so I'm starting with Tier 1, which is a
self-contained fix in one file that I could fully trace and reproduce before claiming it.

**Problem summary:**
The issue occurs in the rag/evaluator/faithfulness_checker.py when a context chunk contains a text field with the value None. The current implementation assumes every text value is a string, so joining the context raises a TypeError instead of handling the missing content gracefully. A successful fix will ensure that None values are treated as empty strings (or otherwise ignored), preventing the crash while allowing the faithfulness check to continue. The related unit test should also pass after the fix.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Yumejichi/pathreview/commit/e4d8229db0bb0849d21cfe29a246d44a63cc5494

**Reproduction summary:**
I reproduced issue #153 by running:

```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker

FaithfulnessChecker().check("Knows Python.", [{"text": None}])
```
The program throws:

```python
TypeError: sequence item 0: expected str instance, NoneType found
```
![alt text](<Pasted Graphic.png>)

This occurs because chunk.get("text", "") returns None when the key exists with a None value, causing " ".join() to fail since the check() function only accepts string type.

**PLAN.md link:** https://github.com/Yumejichi/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md step 2: in `rag/evaluator/faithfulness_checker.py`, the
`context_text` join now uses `chunk.get("text") or ""` instead of `chunk.get("text", "")`, so a
chunk with `{"text": None}` no longer raises a `TypeError` (the `.get` default only covers a
*missing* key, not a key present with value `None`). The existing test
`test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` (already in the repo
from a prior task) now passes, confirming the fix — no new test was needed since that case was
already covered but previously failing.

Before touching code I ran `make test-unit` and `ruff check .` to record a baseline: 53 pre-existing
unit test failures and 182 pre-existing ruff errors across the codebase, all unrelated to this
issue (bias detector, resume parser, review service, etc.). After my change, the suite has 52
failures (one less — the target test now passes) and 376 passes (one more), with no new failures
introduced. `ruff`/`black`/`mypy` on the touched files show only the same pre-existing issues
(unsorted imports in the file's header, an unused variable in an unrelated test method, and
missing third-party type stubs) that existed before my change.

**Next steps:**
Run the full
`make check` self-review, fill out the PR template, mark it ready for review, and add Check-in 2 with the PR link.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/797

**Branch:** `fix/153-faithfulness-checker-none-text`

**What you built:**
Fixed a crash in `FaithfulnessChecker.check()` where a context chunk shaped `{"text": None}` raised a `TypeError` on `" ".join(...)`. The bug was that `chunk.get("text", "")` only falls back to its default when the `"text"` key is *missing*, not when it's present with value `None`.
Changed the lookup to `chunk.get("text") or ""`, which normalizes both cases to an empty string before joining, so the faithfulness check completes normally instead of crashing.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — added `test_mixed_none_and_valid_text_chunks`, which covers a `context_chunks` list mixing valid text with a `{"text": None}` entry.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(Both pass in the sense required by this assignment: the codebase has pre-existing failures unrelated to this issue — 53 unit test failures and 182 ruff errors on `main` before this branch — and my change introduces none of its own. After the fix: unit tests go from
`53 failed, 375 passed` to `52 failed, 377 passed` (the target test plus the new mixed-chunk test both now pass); `ruff`/`black`/`mypy` on the touched files show zero new issues. Full details and
baseline numbers are in the PR description.)*

**Draft PR feedback received from:** none