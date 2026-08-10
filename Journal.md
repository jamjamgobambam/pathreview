## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/153]

**Issue title:** [Faithfulness checker crashes when a context chunk has text: None]

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[test_faithfulness_checker.py's 4 tests failed, and 18 passed. The exact issue is caused at test_none_context_chunk_text - TypeError: sequence item 0: expected str instance, NoneType found. I will need to figure out a way to return a string. A successful issue fix will mean a string gets returned instead of a NoneType. Based on the checklist, I have an overall understanding of the issue. It is not my first open source contribution, however I chose Tier 1. I found the relevant code and the relevant test file. I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.]

**Branch name:** [fix/150-faithfulness_checker]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:** 
[I felt this issue will help me further get comfortable with RAG.]

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 

![Test1](images/1.png)
![Test2](images/2.png)

**Reproduction summary:**
[I reproduced the issue by running tests/unit/test_faithfulness_checker.py. A string is expected to be returned back by the function, but NoneType is being returned.]

**PLAN.md link:** [https://github.com/Sangeetha-007/pathreview/blob/fix/150-faithfulness_checker/PLAN.md]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented test_check_raises_when_chunk_text_is_none() inside of test_faithfulness_checker.py. 

**Next steps:**
The next steps are to complete the following steps in PLAN.md which is to fix check(). 

**Blockers:**
[Anything slowing you down? Or leave blank.]

---

### Check-in 2 (end of week)

**PR link:** : https://github.com/ascherj/pathreview/pull/715

**Branch:**: fix/150-faithfulness_checker

**What you built:**
Fixed a crash in `FaithfulnessChecker.check()` where a context chunk with `text: None` would raise an error during string concatenation. The fix changes `chunk.get("text", "")` to `chunk.get("text") or ""`, since `dict.get`'s default only applies when the key is missing, not when its value is explicitly `None` — the `or ""` now coerces both cases to an empty string before joining.

**Tests added or updated:**
Inside of tests/unit/test_faithfulness_checker.py, I added:
test_check_handles_none_text_mixed_with_valid_chunks: Test that a None-text chunk mixed with valid chunks doesn't crash and still scores using the valid chunk.
test_check_handles_all_none_text_chunks: Test that all-None-text context chunks don't crash and yield a score of 0.0.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
Note*: It passes for the bug I worked on, not for other issues. 

**Draft PR feedback received from:** [name or Slack handle, or "none"]


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer came in. I can get it reviewed by AI, but would prefer a human reviewer. 

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]
Understanding pytests for RAG was the most challenging for me. I never worked with a repo with this many issues listed. Also, I never experienced a ruff error before. This was my first time working with ruff errors. 

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
What I find different about contributing to someone else's production code vs my own project, is the level of responsibility. When it comes to my own personal projects, they are just projects for my own understanding or analysis. However, while contributing to a production code repo, it's best to get everything reviewed and tested more than once. 

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]
AI tools helped me create pytests. Although, I ran and tested the tests myself, I made Claude check once more for edge cases or just in case I forgot anything. Claude did fall short in how it told me to fix all the RAG issues and other issues in the repo before pushing the code for the pull request. I rejected it's suggestions for that. 

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I got sick during the process. If I hadn't gotten sick I would have created the pull request earlier and gotten it reviewed. Another thing I would do differently is read documentation more slowly. This would allow me to get a better picture of the full application, rather than just the faithfulness checker files I worked with. Another thing I would do differently is rely less on AI. 

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]
I am most proud of attempting a RAG pull request. I have done PRs before, but nothing related to AI. This is also my first PR where this many people were interacting. I am also proud of writing docstrings for my test functions!

