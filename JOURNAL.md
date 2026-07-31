## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x ] No — still awaiting review

**Summary of feedback:**
No Feedback 

**How you responded:**
No Feedback 

---

### Reflection

**What was harder than you expected?**
[Be specific — what part of the process, codebase, or workflow
surprised you?]

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]

**How did AI tools help — and where did they fall short?**
[Where was AI assistance most useful this module? Where did you need
to go beyond what AI could give you?]

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]

**What are you most proud of from this module?**
[One thing — it doesn't have to be the PR itself.]


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Replaced all the old regex patterns with new ones that improved the passing rate of the test cases by 25%. (31/32 test cases passed).

**Next steps:**
- trying to reach 100% percentage test case pass by focusing on the current failing test case
- implement hugging face appraoch and compare performance

**Blockers:**
- long regex patterns interfer with the limit on line length but breaking into new lines will affect the performance so have to bypass the format checker.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/289

**Branch:** fix/151/narrow-bias-detector 

**What you built:**
A more flexible regex pattern that detects more biased outputs. All the original patterns for Demographic and Dismissive patterns were replaced with new ones.
The bias detection layer is now more robust.

**Tests added or updated:**
Verified changes were valid by running test_bias_detector.py and passing all test cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** N/A


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/stephanyTF/pathreview/commits/fix/151/narrow-bias-detector/?since=2026-07-16&until=2026-07-16 

**Reproduction summary:**
In the terminal, I ran .venv/Scripts/python -c "from safety.bias_detector import BiasDetector; print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))". 

From there I saw that the test case failed in the output, as the bias detector didn't catched the bias. 

**PLAN.md link:** (https://github.com/stephanyTF/pathreview/blob/fix/151/narrow-bias-detector/PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
N/A

## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/151)

**Issue title:** Bias detector patterns are too narrow to match common phrasings


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
 The issue is that the regex patterns in the bias_detector.py file only match near-exact phrasings, so it misses more natural wordings of the same biased language that the system outputs. An example is when the system is not supposed to assume that bootcamp experience are invaluable, the bias detection fails to pick that sentiment in this: "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education" because the regex is strict on the order and specifity of the flag words. Hence bias prevention is weak without a more robust bias detector.

**Branch name:** fix/151/narrow-bias-detector

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** (Skipped for TF)
