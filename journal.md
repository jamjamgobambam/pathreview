## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace
 #147

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the resume_parser.py, leading indents or whitespaces are forcing new sections to be unaccounted for. Each new line is supposed to be a section but with the indents they are not detected. Once this issue is fixed the parser should be able to detect the correct resume sections even if they contain leading indents or whitespace. 

**Branch name:** fix/147-resume-section-detection-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger 

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sarahmsry/pathreview/commit/761d6152eac0b50556256ac6c1f9de56f65cc6f8

**Reproduction summary:**
In order to reproduce my bug I ran the test cases written for resume_parser.py and I also used other sample tests written by Claude.

**PLAN.md link:** https://github.com/sarahmsry/pathreview/blob/fix/147-resume-section-detection-error/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded] N/A

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
[What have you implemented so far? Which sub-tasks from PLAN.md are done?]
I've gone through the test file and understand where all of the exact issues are arrising. I still have not made any code changes. 

**Next steps:**
[What are you working on for the rest of the week?]
I am working on rewriting the code in resume_parser.py

**Blockers:**
[Anything slowing you down? Or leave blank.]
Not understanding the regex functionality completely in resume_parser.py

---

### Check-in 2 (end of week)

**PR link:** [link to your submitted pull request]

**Branch:** [the branch name you worked on, e.g. `fix/123-short-description`]

**What you built:**
[1–3 sentences summarizing what your fix does and how it works]

**Tests added or updated:**
[Which test files did you touch? What do they cover?]

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]