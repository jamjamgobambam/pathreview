## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** #151: Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The safety module's bias detector (`safety/bias_detector.py`) uses strict, narrow regular expression patterns to flag biased or dismissive language. Because of this, it fails to match common phrasings (such as plural developer terms, verbs like "can't write" for bootcamps, or missing/incorrectly structured optional matches). A successful fix will expand and generalize these regex patterns so they correctly capture all variations tested in the test suite without triggering false positives on positive or neutral statements.

**Branch name:** fix/151-bias-detector-patterns

**Setup confirmation:** [x] App runs locally at `localhost:5173`

**Cohort ledger:** [x] Issue added to cohort ledger
