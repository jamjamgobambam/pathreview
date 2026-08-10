# PathReview Development Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker combines retrieved context into a single string before evaluating responses. If one of the context chunks contains a `text` field with the value `None`, the checker crashes because it attempts to join a non-string value. A successful fix will safely handle missing or `None` text values so the evaluation can continue without raising an error.

**Branch name:** `fix/153-faithfulness-none-context`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

### Is this issue right for me? 
Yes! I chose this issue because it is a manageable first open-source contribution that still requires real debugging and testing. Although the fix appears relatively small, I will need to understand how the faithfulness checker processes context and why the crash occurs before implementing a solution. This issue fits my current Python experience and will help me become more comfortable working in a larger codebase.

This issue has a clearly defined bug, a known failing test, and a limited scope, making it a good first open-source contribution. It requires debugging an existing codebase, understanding the cause of the crash, implementing a safe fix, and verifying it with automated tests. Since it is a Tier 1 issue, it is an appropriate starting point while still providing experience working with a larger project.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ascherj/pathreview/commit/06f132bf497e1620de48d64fe8d0edd282257369 

**Reproduction summary:**
I reproduced the issue by running the existing unit test `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py`. The test failed because the faithfulness checker attempted to join a `None` value with strings, confirming that context chunks with `text: None` cause a `TypeError`.

**PLAN.md link:** https://github.com/ashna2007/pathreview/blob/fix/153-faithfulness-none-context/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I still need to confirm whether the intended behavior is to skip chunks with `None` text or treat them as empty strings, although the issue description suggests safely converting them to empty strings.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #153 by updating the faithfulness checker to safely handle context chunks whose `"text"` field is `None`. I verified that the previously failing test now passes, and the full unit test results improved from 53 failures and 375 passes to 52 failures and 376 passes.

**Next steps:**
Push my branch, open a draft pull request, complete the PR template, request peer or mentor feedback, address any feedback I receive, and finalize the pull request.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/665

**Branch:** `fix/153-faithfulness-none-context`

**What you built:**
Implemented a fix for Issue #153 by updating the faithfulness checker to safely handle context chunks whose `"text"` field is `None`. This prevents a `TypeError` during context concatenation while preserving the existing behavior for valid text.

**Tests added or updated:**
No new tests were added. The existing unit test `test_none_context_chunk_text` now passes after the fix. I also verified that `make test-unit` improved from 53 failed / 375 passed to 52 failed / 376 passed.

**Self-review confirmation:**
- [x] `make check` introduces no new failures (182 pre-existing errors remain)
- [x] `make test-unit` introduces no new failures (improved from 53 failed to 52 failed)

**Draft PR feedback received from:**
none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No review came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
Trying to understand how my issues fits into the codebase was very difficult. It took the longest amount of time, considering the fact that there were multiple failing tests, yet there was only one relevant to mine. I thought that because it was a small issue, it would be easy to follow and find, and as a result, underestimated how much time it would take to find that issue and understand what was going on. 

**What did you learn about working in a large codebase?**
One of the most significant things I learned from this entire process is that even as something small as a tier one issue, a single line code change, can be so important. When building your own project, you don't pay attention to the single line changes, but with a large codebase, since every little thing is very significant to the entire functionality, it's more important even though it may not feel like it.

**How did AI tools help — and where did they fall short?**
AI assistance was the most useful when trying to understand the codebase. It is a very large codebase, and my contribution was so small, so locating where my issue was and understanding where to start was crucial. Claude helped me intially navigate what I was working with, and it made my life much easier. However, it did fall short when it came to locating the specific test I needed, so prompting that a little bit more and replicating the issue were the steps I had to take to fix that.


**What would you do differently if you started over?**
I think planning would be the biggest change I would make. This issue was interesting and significant, but I overestimated the amount of time it would take. If I started again, I would've completed this issue much quicker and tried completing another one as well.

**What are you most proud of from this module?**
I think the fact that I was able to understand how relevant a simple fix can be to fixing the entire issue is the thing I am most proud of. Without my fix, the RAG would not be able to work, eventually propagating into a bigger issue that hinders the functionality of the app. Open source contributions, big or small, make huge changes overall, and that's what made me proud of the small yet mighty work I did.