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

**Self-review confirmation:** [ X ] make check passes  [ X ] make test-unit passes

**Draft PR feedback received from:** none, I have received none

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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in on the draft PR by the end of the week, despite opening it
early and sharing the link. The PR remained open and awaiting review through
the submission deadline.

**How you responded:**
No feedback to respond to. Ahead of submission I did a final self-review against
CONTRIBUTING.md — confirmed the branch name and Conventional Commits message
format, re-ran the full unit suite and `make check` to re-confirm the before/
after baselines, and made sure the pre-existing failures were documented in the
PR description so a reviewer could quickly see my change introduces none.

---

### Reflection

**What was harder than you expected?**
The environment setup, not the code. The fix itself was one line, but getting to
the point where I could *run* the test took the longest: pytest wasn't on my
PATH, my Python was pointing at a global 3.14 install instead of a venv, and when
I finally tried to activate a venv I got a "command not found" error because I was
typing a PowerShell-style path into a bash shell. None of that was the "real"
task, but it was most of the friction. The other genuinely tricky moment was
diagnostic, not technical: at one point the reproduction test *passed* when it
should have failed, because I'd already edited the file earlier without realizing
it. I nearly built a whole week's reproduction around a bug that wasn't in a
broken state. That taught me to always confirm the actual on-disk state before
trusting a test result.

**What did you learn about working in a large codebase?**
The biggest shift from my own projects is that "passing tests" isn't a binary you
control. This codebase had 52 failing unit tests and 363 check errors before I
touched anything — none related to my issue. In my own projects a red suite means
I broke something; here it meant I had to establish a baseline first, then prove
my change moved the numbers in the right direction (53→52 failures) and introduced
nothing new. That reframes the whole standard of "done": it's not "everything is
green," it's "I didn't make it worse, and I can prove it." I also learned to trust
scope — three tests in the very file I edited were failing, and the instinct was to
fix them too, but they were in a different code path (`_extract_claims` /
`_is_supported`) and fixing them wasn't my issue. Staying scoped and documenting
the rest was the right call.

**How did AI tools help — and where did they fall short?**
AI was most useful for the diagnostic reasoning — explaining *why* `dict.get("text",
"")` returns `None` for a present-but-null key (the default only fires on missing
keys), and why `chunk.get("text") or ""` fixes the None case, the missing-key case,
and empty strings all at once. That saved me from a clumsier `if/else` or
`try/except`. It was also good for environment troubleshooting — spotting that my
shell was bash, not PowerShell, from the shape of the error. Where it fell short:
it couldn't see the actual state of my files or run my tests, so when the test
passed unexpectedly, AI could only *guess* why until I ran `grep` and `git diff`
myself. The truth about what was on disk had to come from me. AI could reason about
the code; it couldn't observe my environment.

**What would you do differently if you started over?**
Two things. First, I'd set up the venv and confirm `python -m pytest` worked on
day one, before doing anything else. It was a bit time consuming when I forget that 
this is something I have to consistently do when reopening the project. Second, I'd 
request PR feedback earlier and more actively. I opened the draft PR but no review 
came, and in hindsight I could have pinged specific people in Discord earlier in the 
week rather than waiting, which might have surfaced something I missed.

**What are you most proud of?**
Not the fix as it's just one line. What I'm proud of is the rigor around it: establishing
a real before/after baseline on both the test suite and `make check`, correctly
identifying which failures were mine to care about and which weren't, and
documenting all of it so anyone reviewing could verify in seconds that my change is
safe. The discipline of proving "no new failures" in a messy codebase felt like the
actual skill this module was teaching.
