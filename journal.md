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
[Anything you're still uncertain about going into Week 9, or leave blank]
