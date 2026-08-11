## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method in `rag/evaluator/faithfulness_checker.py`
builds a combined context string by calling `chunk.get("text", "")` on each
retrieved context chunk. This works fine when the `"text"` key is missing
entirely, but if a chunk has the key present with a value of `None`,
`.get()` returns `None` instead of the default, since the default only
applies to missing keys. The subsequent `" ".join(...)` call then fails
with a `TypeError` because it can't join a `None` into a string. A
successful fix will make `check()` handle a `None` chunk text value
gracefully (e.g. treating it as an empty string) instead of crashing,
matching the existing test `test_none_context_chunk_text` in
`tests/unit/test_faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Reproduction — Issue #153

**Observed:** `faithfulness_checker.py` raises a `TypeError` when a claim
verification result contains `None` values in fields normally accessed via
`dict.get(...)`. `.get()` returns `None` when a key is missing or explicitly
set to `None` — the code downstream assumed a string/number and called
methods on it (e.g. string formatting, arithmetic, comparisons) without a
None-check, so the crash surfaces whenever the LLM response or upstream
data omits a field the checker expects.

**Steps to reproduce:**

1. Ran the faithfulness evaluator on a sample with a claim whose scoring
   result had one or more fields missing/None.
2. Confirmed the `TypeError` traceback pointed to the `.get()` call site in
   `rag/evaluator/faithfulness_checker.py`.
3. Verified the crash is deterministic given that input — not intermittent.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [[link to your commit — add the actual URL](https://github.com/Rosman-h/pathreview/commit/c30955a77934d6453d7926a929c9b506a8131d5a)]

**Reproduction summary:**
Reproduced the TypeError in `rag/evaluator/faithfulness_checker.py` by running
the checker on a claim result with None/missing fields; confirmed `.get()`
returns None and downstream code doesn't guard against it before use.

**PLAN.md link:** [[link to PLAN.md on your branch](https://github.com/Rosman-h/pathreview/blob/fix/153-faithfulness-checker-none-crash/PLAN.md)]

**Walkthrough video (recommended):** [optional]

**Blockers or open questions:**
Fix for this issue was already implemented on `fix/153-faithfulness-checker-none-crash`
during Week 7 work; documenting reproduction/plan here reflects that process
retroactively. Open question: whether the correct fallback behavior (skip vs.
0-score vs. typed error) matches what other callers expect — worth confirming
with maintainer feedback on the PR.

## Week 9 — Mid-week progress

**Status:** Core fix for #153 implemented and tested. Added `_safe_chunk_text`
helper to `FaithfulnessChecker` to guard against three failure modes:
non-dict chunks, None text values, and non-string text values (e.g. int).
7 new regression tests added and passing.

**Pre-existing issue found (out of scope):** While testing, found that
`_is_supported()` has a stricter overlap threshold than 3 existing tests
assume — `test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, and `test_multiple_claims_varying_support`
fail even on the original, unmodified code (confirmed via `git stash`).
This appears unrelated to #153 and is not something I'm fixing in this PR
to keep scope contained. Flagging here and will mention in the PR
description in case a maintainer wants a separate issue filed.

**Remaining for this week:** Final documentation pass, full test suite run,
and PR submission.

## Week 9 — Submission

**PR link:** [[paste your actual PR URL once opened](https://github.com/ascherj/pathreview/pull/369)]

**Summary:** Implemented `_safe_chunk_text()` in `FaithfulnessChecker` to
guard against non-dict chunks, None text, and non-string text — closing
the remaining gaps from the original #153 crash. Added 7 regression tests
covering these cases, all passing.

**Verification:** Ran the full test suite before and after this change
(via checkout of the prior commit) — confirmed identical 52 pre-existing
failures unrelated to this work in both cases, and this PR adds 7 new
passing tests with no regressions.

**Known out-of-scope issues found and documented (not fixed):**

- 3 pre-existing test failures in this file caused by `_is_supported()`'s
  overlap threshold, unrelated to #153
- Pre-existing missing type annotations / unused variable in this test
  file, flagged to reviewers rather than silently fixed

**Reflection:** The core fix was small, but confirming scope (what's mine
to fix vs. pre-existing) took the most time this week. Worth it — avoided
scope creep into unrelated code.
## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #369 by the end of the week. Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a sign the PR was ignored.

**How you responded:**
N/A — no feedback to respond to. I re-read my own PR description and diff one more time as a stand-in for review, and confirmed the regression tests still pass against the current state of the branch before final submission.

---

### Reflection

**What was harder than you expected?**
Getting the local dev environment running was harder than the actual fix. I lost most of Week 7 to Windows-specific friction — Git Bash vs. PowerShell syntax differences, installing GNU Make through winget, getting WSL2 and Docker Desktop to actually put things on PATH. The `None`-crash bug itself in `faithfulness_checker.py` was a small, well-scoped fix once I could run the test suite locally. The ratio of environment setup time to code-change time was lopsided in a way I didn't expect going in — I assumed most of the week would go to understanding the RAG evaluator logic, not to getting `make test` to execute at all.

**What did you learn about working in a large codebase?**
The fix itself was maybe 15 lines, but making it production-quality meant thinking about every caller of the function, not just the one that happened to crash. Adding `_safe_chunk_text()` and handling non-string `text` values and non-dict chunk entries came from tracing how the function was actually called elsewhere in the codebase, not from the original issue description. In my own projects I fix the case in front of me. Here I had to assume inputs I hadn't seen yet would eventually hit this code path, because I wasn't the only one calling it and I couldn't predict every caller. I also learned to respect pre-existing test/lint debt as out of scope — `git stash`-ing to confirm failures predated my branch, documenting them, and moving on rather than trying to fix everything I touched.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical layers: diagnosing PowerShell/Git Bash syntax mismatches fast, writing regression tests that matched the project's existing test conventions once I pointed to examples, and drafting PLAN.md and JOURNAL.md structure so I could focus on content instead of format. It fell short on judgment calls specific to this codebase — deciding what counted as in-scope for issue #153 versus scope creep, and deciding how defensive `_safe_chunk_text()` needed to be without over-engineering it. Those decisions needed me to actually read the surrounding code and reason about the project's conventions, not just pattern-match to "how would I fix this in isolation."

**What would you do differently if you started over?**
I'd spend less time retroactively reconstructing Week 8's PLAN.md and reproduction docs after the fact, and instead write them concurrently with the fix in Week 7. Writing documentation after the code is already working meant reconstructing my own reasoning from memory instead of capturing it live, which made the PLAN.md feel more like an artifact than a real plan. I'd also budget explicit time for environment setup up front instead of treating it as an unplanned detour — on Windows it's predictable enough at this point that it deserves its own line item.

**What are you most proud of from this module?**
Diagnosing that the pre-existing test and lint failures were out of scope rather than something I broke. It would have been easy to either ignore them or spend the rest of the module trying to fix unrelated debt. Using `git stash` to isolate my changes and confirm the failures existed on the base branch, then documenting that clearly instead of silently working around it, is the part of this module that felt most like actual engineering judgment rather than following a checklist.
