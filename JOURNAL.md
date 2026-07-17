## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue]

**Reproduction summary:**
In the terminal, I ran .venv/Scripts/python -c "from safety.bias_detector import BiasDetector; print(BiasDetector.detect_bias('The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education'))". 

From there I saw that the test case failed in the output, as the bias detector didn't catched the bias. 

**PLAN.md link:** [link to PLAN.md in your fork]

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — shared for early feedback]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]


## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/151)

**Issue title:** Bias detector patterns are too narrow to match common phrasings


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
 The issue is that the regex patterns in the bias_detector.py file only match near-exact phrasings, so it misses more natural wordings of the same biased language that the system outputs. An example is when the system is not supposed to assume that bootcamp experience are invaluable, the bias detection fails to pick that sentiment in this: "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education" because the regex is strict on the order and specifity of the flag words. Hence bias prevention is weak without a more robust bias detector.

**Branch name:** fix/151/narrow-bias-detector

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** (Skipped for TF)