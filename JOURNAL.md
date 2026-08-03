## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: changed the context-concatenation line in
`FaithfulnessChecker.check()` from `chunk.get("text", "")` to
`chunk.get("text") or ""`, so a chunk with `text: None` is coerced to an empty
string instead of crashing `" ".join()`. All PLAN.md sub-tasks are done — fix
applied, target test passing, missing-key test still passing, full suite run.

**Next steps:**
Open a draft PR, request peer/mentor feedback, address any comments, then mark
ready for review and submit.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/495 

**Branch:** fix/153-faithfulness-none-chunk-text

**What you built:**
A one-line fix in `rag/evaluator/faithfulness_checker.py`. The `check()` method
built its context with `chunk.get("text", "")`, but `dict.get()`'s default only
applies to missing keys — so a chunk of `{"text": None}` returned `None` and
crashed `" ".join()` with a TypeError. Using `chunk.get("text") or ""` coerces
any null (or otherwise falsy) text value to an empty string before joining.

**Tests added or updated:**
No new test files. The fix is validated by the pre-existing
`test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py`,
which reproduced the crash and now passes; `test_missing_text_key_in_chunk`
continues to pass.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
(codebase has documented pre-existing failures — 52 test failures, 363 check
errors — present before and after this change; this PR introduces no new
failures and resolves one: 53→52 test failures, 363→363 check errors. See PR
description for the full before/after baseline.)

**Draft PR feedback received from:** [paste reviewer name/Slack handle, or "none"]

## Summary
Fixes #153 — `FaithfulnessChecker.check()` raised `TypeError` when a context
chunk had `text: None`.

## Root cause
`check()` built context via `chunk.get("text", "")`. A `dict.get()` default only
applies to *missing* keys, so a chunk of `{"text": None}` returned `None`, which
flowed into `" ".join(...)` and raised
`TypeError: sequence item 0: expected str instance, NoneType found`.

## Fix
Changed the expression to `chunk.get("text") or ""`, coercing any falsy value
(including `None`) to an empty string. One-line change in
`rag/evaluator/faithfulness_checker.py`; covers the `None` case, the missing-key
case, and empty strings in one expression.

## Testing
- `test_none_context_chunk_text` (reproduces the bug) now passes.
- `test_missing_text_key_in_chunk` continues to pass.
- Full unit suite before: 53 failed, 375 passed. After: 52 failed, 376 passed.
- `make check` before and after: 363 errors, unchanged.

My change resolves exactly one test (the target) and introduces no new failures
or check errors.

## Pre-existing failures (unrelated to this PR)
The codebase has 52 pre-existing unit-test failures and 363 pre-existing
`make check` errors, all unrelated to this issue and present both before and
after my change. Within `test_faithfulness_checker.py`, three tests remain
failing before and after — `test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support` — all in
the claim-extraction/support-matching logic (`_extract_claims` /
`_is_supported`), a code path this PR does not touch.
