## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** Tier 1

**Problem summary:**
`BiasDetector.detect_bias()` in `safety/bias_detector.py` relies on a small set of rigid regexes that only match near-exact phrase orderings (e.g. "bootcamp education is insufficient"), so it misses the same bias expressed in more natural phrasing, such as "bootcamp graduates can't write production code" or "young developers can't handle complex systems." As a result, 9 of the tests in `tests/unit/test_bias_detector.py` currently fail, meaning dismissive-education and demographic-assumption bias can slip past the safety layer undetected in generated feedback. A successful fix reworks the `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` regex lists (or the matching approach) to catch these common phrasing variations — covering verbs like "can't"/"lack"/"struggle" and subject variants like "developers"/"programmers"/"graduates" — while still passing the existing tests that assert neutral/positive mentions of bootcamps or educational background are not flagged.

**Branch name:** fix/151-bias-detector-too-narrow

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger