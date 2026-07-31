## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker in the RAG evaluator (rag/evaluator/faithfulness_checker.py)
verifies that AI-generated claims are supported by retrieved context. It builds the
context string with chunk.get("text", ""), but .get() only falls back to the default
when the key is missing — if "text" exists with a value of None, it returns None, and
the " ".join(...) call raises a TypeError. Right now any chunk with a null text field
crashes the whole check instead of being handled. A successful fix treats None text
as an empty string (or skips the chunk) so the checker degrades gracefully, and makes
the failing test test_none_context_chunk_text pass.

**Selection notes:** Tier 1 fits my current familiarity with the codebase — the bug is
isolated to one function, has exact reproduction steps, and an existing failing test
defines "done," so the scope is well-bounded per the "Is this issue right for me?" checklist.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [0c7a92f](https://github.com/nuv2453-ah/pathreview/commit/0c7a92f)

**Reproduction summary:**
Reproduced the issue by running `FaithfulnessChecker().check('Knows Python.', [{'text': None}])` in a local Python shell — confirmed it raises `TypeError: sequence item 0: expected str instance, NoneType found` on line 34 of `rag/evaluator/faithfulness_checker.py`. Also confirmed the failing test `test_none_context_chunk_text` in `make test-unit` shows the same crash.

**PLAN.md link:** [PLAN.md](https://github.com/nuv2453-ah/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to grep for other `.get("text", "")` occurrences in the codebase to check if the same pattern exists elsewhere.
## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: changed `chunk.get("text", "")` to `chunk.get("text") or ""` in `faithfulness_checker.py`. Confirmed `test_none_context_chunk_text` now passes. Verified no new test failures introduced (52 pre-existing failures, down from 53).

**Next steps:**
Open draft PR on ascherj/pathreview and request peer review via Slack.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/435

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Changed `chunk.get("text", "")` to `chunk.get("text") or ""` in the `context_text` list comprehension inside `FaithfulnessChecker.check()`. This ensures chunks with explicit `"text": None` are treated as empty strings instead of crashing `" ".join()` with a `TypeError`.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — pre-existing test `test_none_context_chunk_text` now passes; no new failures introduced.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (52 pre-existing failures unchanged; fix resolves 1)

**Draft PR feedback received from:** [add name after you get Slack review]
