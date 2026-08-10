# Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds context by pulling `text` out of each chunk with `chunk.get("text", "")`. That default only applies when the key is missing entirely, whereas if `text` is present but set to `None`, `.get()` returns `None` instead of falling back to an empty string. The code then tries to join all chunk texts together with `" ".join(...)`, which raises a `TypeError` since you can't join a `None` value into a string. This lives in `rag/evaluator/faithfulness_checker.py`. It matters because a chunk with `text: None` is a plausible ingestion artifact, not a rare edge case, so right now it silently crashes faithfulness checking instead of treating the chunk as empty content like the empty string case

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes — "Is this right for me?" checklist**

**Part 1 — Understanding the Issue**
- Can explain it without re-reading: `check()` builds context text from chunks using `chunk.get("text", "")`, but that default only fires when the key is missing, not when it's present with value `None`. So a chunk like `{"text": None}` passes straight through, and the later `" ".join(...)` call crashes with `TypeError`.
- Located the relevant code: `rag/evaluator/faithfulness_checker.py`, in `check()`.
- Done looks like: passing `[{'text': None}]` as a context chunk no longer crashes, it's treated as empty text, same as the missing-key case. `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` should pass.

**Part 2 — Tier Fit**
- Labeled `tier-1` on GitHub. This is my first open-source contribution, so a Tier 1 self-contained fix is the right level: one function, one file, no cross-module reasoning required.

**Part 3 — Codebase Readiness**
- Read `check()` and the surrounding context-building logic in `faithfulness_checker.py`.
- Rough fix plan: replace `chunk.get("text", "")` with `chunk.get("text") or ""` so both a missing key and an explicit `None` value fall back to an empty string.
- Found and read `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` to confirm what the test expects before writing any code.

**Part 4 — Scope and Time**
- Checked the issue comments and ledger: 3 other students are also on #153, plus an open PR (#162) referencing it. Per the checklist, claims are non-exclusive and grading is based on my own artifacts, so I'm fine proceeding — I'll write my own fix and tests independently rather than referencing the existing PR.
- Time estimate: this is a one-line fix plus getting one named test passing — well under the 3–6 hour Tier 1 window, so it's realistic for Weeks 8–9 alongside my other coursework.
- No blockers: issue body names no dependency on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kacp3rrr/pathreview/commit/30ce358697d819085967aec917661d22445e4b08

**Reproduction summary:**
Ran the existing test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checkcer.py`, which fails with `TypeError: sequence item 0: expected str instance, NoneType found` at line 34 of `faithfulness_checker.py`. The crash occurs in `context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])` when a chunk has `text: None`, since `.get()`'s default only accounts for missing keys, not explicit `None` values, which cause a type error when joining with a string.

**PLAN.md link:** https://github.com/kacp3rrr/pathreview/blob/fix/153-faithfulness-none-text-crash/PLAN.md

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all the sub-tasks from PLAN.md: changed line 35 in `rag/evaluator/faithfulness_checker.py` from `chunk.get("text", "")` to `chunk.get("text") or ""`, confirmed `test_none_context_chunk_text` now passes, and ran the full `make test-unit` suite before and after to verify no regressions (53 failed/375 passed before, 52 failed/376 passed after — only that one test changed status). Also ran `make check` and confirmed the 182 pre-existing lint errors are identical before and after my change, so nothing new was introduced.

**Next steps:**
Opening the PR, filling in the PR template with the fix description, before/after test evidence, and get it marked ready for review

**Blockers:**
None

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/845

**Branch:** fix/153-faithfulness-none-text-crash

**What you built:**
Fixed a `TypeError` in the faithfulness checker's `check()` method, where a context chunk with `text: None` crashed the context-joining step. Changed `chunk.get("text", "")` to `chunk.get("text") or ""` so both a missing key and an explicit `None` value normalize to an empty string.

**Tests added or updated:**
No new test file created; verified the existing test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py`, which covers a context chunk with `text: None`, now passes after the fix.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(any stray errors are unrelated to this fix, and the fix did not introduce any new errors, only cleared the failing test that was related to the original issue)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No

**Summary of feedback:**
N/A

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
All the surrounding process behind submitting a pull request, and all the intricacies that needed to be taken into account. This includes following a specific template, having to verify a number of tests, and more generally just the breadth of checks that needed to be done before going ahead with the pull request. Given it was my first time doing something like this with a pull request, the contrast between the simple nature of the change and the process that goes behind it is something that I was surprised by, but ultimately satisfied with once I got it down. I imagine it gets easier as you do it, but for my first time it was quite the surprise just how much actually goes behind a pull request and the CI workflow.

**What did you learn about working in a large codebase?**
As noted above, I learned a lot about the CI workflow that goes into submitting changes in a large codebase. To be specific, given this project had a myriad of other issues (intentionally for other students to solve), learning to navigate around those, and be ultra careful about my scope of things was something that was new to me, given most of my previous experience was working in a codebase by myself or with a few people at max, where I was hands on with every single issue and had a larger understanding of every issue. It was genuinely new to have to accept not necessarily understanding those other issues, but also moreover understanding where the scope of my specific issue started and ended.

**How did AI tools help — and where did they fall short?**
They helped in making sure I was tidy with the semantics of submitting a pull request, as well as understanding the potential scope of this issue and where it could potentially manifest elsewhere. However, it wasn't able to really do that exploration too effectively on its own, especially with the multitude of other issues it tripped up on, so that exploration was (and for the better) left up to me.

**What would you do differently if you started over?**
I would choose a slightly harder module that required a bit more work and a wider scope, as well as trying to get to a point where the workflow for a pull request was streamlined, and where I'm more hung up on the actual issue instead of the pull request, not vice versa as I was here, given it was my first time.

**What are you most proud of from this module?**
Understanding the process behind a pull request and understanding the usefulness of Git/GitHub as a collaborative tool a lot better than I previously did.
