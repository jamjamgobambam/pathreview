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