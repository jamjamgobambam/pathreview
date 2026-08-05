## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [*] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue is faithfulness checker builds context from text from chunks and it currently uses chunk.get("text",""), but if the chunk contains "text": None the .get() call returns None and "".join() raises a type error. It crashes on valid chunk structures that include None values instead of text. The fix would be to normalize None to an emptu string before joing, allowing the checker these chunkks gracefuly and the existing unit test passing.

**Branch name:** fix/153-faithfulness-checker-crashes

**Setup confirmation:** [*] App runs locally at localhost:5173

**Cohort ledger:** [*] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ibs12/pathreview/commit/99bf412

**Reproduction summary:**
I reproduced the issue by running the faithfulness checker unit tests with a chunk whose text field is None. The current implementation raises a TypeError when it joins context chunks because it does not normalize None to an empty string before concatenation.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** Not recorded yet.

**Blockers or open questions:**
I am still confirming whether any other evaluator paths rely on chunk text being a non-None string before I move into the implementation phase.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The None-handling fix is implemented in the faithfulness checker, and the targeted regression tests for None-valued chunk text are now passing locally.

**Next steps:**
I am validating the change against the repository’s standard checks and preparing the PR details and journal entry for submission.

**Blockers:**
The broader repository has existing lint/type issues outside this fix, so I am documenting that the targeted regression remains green while the project-wide check still reports unrelated failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/542

**Branch:** `fix/153-faithfulness-checker-crashes`

**What you built:**
I updated the faithfulness checker to normalize `None` chunk text to an empty string before building the context string, so the evaluator no longer crashes on valid chunk objects with `text: None`.

**Tests added or updated:**
I added regression coverage in `tests/unit/test_faithfulness_checker.py` for None-valued chunk text and the missing-text-key case.

**Self-review confirmation:** [ ] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided for this submission in Summer 2026, so there was no external review to respond to.

**How you responded:**
No changes were needed based on reviewer feedback.

---

### Reflection

**What was harder than you expected?**
The hardest part was staying focused. The issue itself was small, but the repo had a lot of other problems around it, so it was easy to get pulled into unrelated stuff.

**What did you learn about working in a large codebase?**
I learned that contributing to someone else’s project is about being careful and keeping your change scoped. It is not just about fixing the bug; it is also about following the project’s patterns and not making the change bigger than it needs to be.

**How did AI tools help — and where did they fall short?**
AI helped me find the right part of the codebase and understand the bug faster. It was less helpful when I had to decide what to ignore and what to keep focused on, especially because there were other existing issues in the repo.

**What would you do differently if you started over?**
I would spend a little more time reading the surrounding tests and patterns before I changed anything. That would probably make the implementation step smoother and help me avoid getting distracted by unrelated issues.

**What are you most proud of from this module?**
I’m proud that I was able to reproduce the bug, fix it in a focused way, and finish the whole contribution process from planning to PR submission.

