## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** #151: Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The safety module's bias detector (`safety/bias_detector.py`) uses strict, narrow regular expression patterns to flag biased or dismissive language. Because of this, it fails to match common phrasings (such as plural developer terms, verbs like "can't write" for bootcamps, or missing/incorrectly structured optional matches). A successful fix will expand and generalize these regex patterns so they correctly capture all variations tested in the test suite without triggering false positives on positive or neutral statements.

**Branch name:** fix/151-bias-detector-patterns

**Setup confirmation:** [x] App runs locally at `localhost:5173`

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [[Link to reproduction commit](https://github.com/LilRed92/pathreview/commit/a7b287dbf643c6b402735f39bbe9bdae1f269d02)]

**Reproduction summary:**
I reproduced the issue programmatically by creating a standalone script (`reproduce_bias.py`) that imports `BiasDetector` and runs failing phrasings (such as plural developer forms and capability verbs) directly through it. The script confirmed that the current regex patterns miss these cases. I also added a TODO warning comment in `safety/bias_detector.py` to document this.

**PLAN.md link:** [[Link to PLAN.md](https://github.com/LilRed92/pathreview/blob/fix/151-bias-detector-patterns/PLAN.md)]

**Walkthrough video (recommended):** [[Link to walkthrough video](https://www.loom.com/share/de030fd88b424fc787dc7a8db6549b51)]

**Blockers or open questions:**
None. The reproduction script isolates the exact pattern failures, making testing and verification highly reliable.
