## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/151](https://github.com/ascherj/pathreview/issues/151)

**Issue title:** Bias detector patterns are too narrow to match common phrasings 

**Tier:** [✓] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The file `bias_detector.py` uses regex patterns to detect bias. This means that statements with the same sentiment but different word orderings would not be flagged for bias. We will likely have to rely on a different method of detection that does not require near-exact sentence matching. 

**Branch name:** `fix/151-bias-detector-too-narrow`

**Setup confirmation:** [✓] App runs locally at localhost:5173

**Cohort ledger:** [✓] Issue added to cohort ledger



## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/carlinnv/pathreview/tree/fix/151-bias-detector-too-narrow](https://github.com/carlinnv/pathreview/tree/fix/151-bias-detector-too-narrow)

**Reproduction summary:**
I reproduced the issue by running the test suite. I found that 9 out of the 32 tests passed. The ones that failed typically failed because the regex used to detect biased sentences were too rigid to capture the full range of sentence diversity. 

**PLAN.md link:** [Link to PLAN.md](https://github.com/carlinnv/pathreview/blob/fix/151-bias-detector-too-narrow/PLAN.md)

<!-- **Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] -->

**Blockers or open questions:**
One thing that stood out to me was that in one of the tests, a factual observation was flagged as biased, while a biased assumption was not. Something that I want to consider is how I can ensure that all biased sentences are captured while also keeping a balance and making sure that factual observations do not get flagged as biased. 



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have currently implemented the expanded regex patterns and semantic heuristic check. I also checked against the test set and specifically looked for whether or not the new bias detector system is too strict. 

**Next steps:**
I am going to work on the pull request and making edits before submitting. 

**Blockers:**

---

### Check-in 2 (end of week)

**PR link:** [Link to pull request](https://github.com/ascherj/pathreview/pull/770)

**Branch:** fix/151-bias-detector-too-narrow

**What you built:**
I expanded the bias detector's regex patterns so they catch more common wording variations around bootcamps, self-taught backgrounds, and demographic assumptions. I also added a semantic heuristic check that looks through feedback sentence-by-sentence and flags a protected-background term when it appears alongside a negative capability claim and a competence-related term.

**Tests added or updated:**
`tests/unit/test_bias_detector.py` was updated to cover the broader regex matches, the semantic fallback, and the non-biased cases that should stay unflagged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [✓] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
I think the hardest part of this project was understanding the codebase. Part of the task was learning how to delve into and understand a large codebase by reading the documents and using the tools available to us. 

**What did you learn about working in a large codebase?**
I learned that AI can be a fantastic tool for working in a large codebase. I used it to summarize specific functions within files and also scan for dependencies to see how each file links to one another. 

**How did AI tools help — and where did they fall short?**
I used AI to get familiar with the files within the codebase I was working with. It was also a really good tool when it came to suggesting implementations, because there were definitely times I wanted to achieve a certain feature but wasn't able to. 

**What would you do differently if you started over?**
Although I hit the deadlines on time, I would have started over so I could get feedback on my PR. I think it is definitely important to learn not just how to write documents such as PRs but also to respond to them professionally. 

**What are you most proud of from this module?**
I am most proud of myself for learning how exactly PR works. In the future, I will definitely use things like the pull request template in the .github folder to make contributions to my own projects easier. 