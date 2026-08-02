## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/151)]

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

In safety/bias_detector.py we see regex patterns used here to create bias detectors. These bias detectors are too narrow and are misclassifying common phrases. A successful fix will widen regex patterns to detect common phrases instead of looking at specific phrases to detect bias. 

**Branch name:** [paste branch name here]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

<br>
<br>


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [[link to commit documenting the reproduced issue](https://github.com/snugcoder/pathreview/commit/54a5200621d29914b07fee43eba33661a745bfad)]

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]
I reproduced the issue by running the test suite. I observed that the bias patterns were too specific and caused the test cases to fail. 

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]
<br>
<br>

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[I have implemented all steps from PLAN.md]

**Next steps:**
[I am working on any additional testing that may be needed before closing this PR]

**Blockers:**
[Only my PC]

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** `fix/safety/151-expanding-bias-detector-patterns`

**What you built:**
[This fix included creating a new system for determining bias patterns. Instead of strict regex pattern matching, the bias_detector.py file now uses a series of input normalization and cleaning, before checking its phrases against a dictionary of phrases. To be determined as biased, it must match at least 6 words from the dictionary. It also takes into account dismissive phrases such as not, lack, etc, to be as accurate as possible for bias detection.]

**Tests added or updated:**
I had to update all the tests in order to pass make check and CI, but I added new test cases testing different cases in phrasing, whitespace, precise phrasing found in the dictionary, as well as words not placed into the dictionary. 

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** N/A

<br>
<br>

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
Understanding which components were needed for bias detection. It was hard to understand how the different pieces fit in at first, but eventually it started to make sense. 

**What did you learn about working in a large codebase?**
Contributing to a large codebase requires conscious development -> continuous integration, robust testing, and pull requests to ensure that fixes and features are correct and apply to the correct changes to the right places. 

**How did AI tools help — and where did they fall short?**
AI tools helped to determine the shortcomings of REGEX (in my case) and what patterns to include in semantic bias detection for recognition within the already existing frame of development. It was bad at understanding the context of the codebase even with the knowledge of the codebase. I wou

**What would you do differently if you started over?**
I would pick another tier that connects to more parts within the codebase to learn more about the codebase. 

**What are you most proud of from this module?**
I am most proud of being able to connect all the moving parts in the project. 