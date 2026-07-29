## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** Tier 1

**Problem summary:**
`BiasDetector.detect_bias()` in `safety/bias_detector.py` relies on a small set of rigid regexes that only match near-exact phrase orderings (e.g. "bootcamp education is insufficient"), so it misses the same bias expressed in more natural phrasing, such as "bootcamp graduates can't write production code" or "young developers can't handle complex systems." As a result, 9 of the tests in `tests/unit/test_bias_detector.py` currently fail, meaning dismissive-education and demographic-assumption bias can slip past the safety layer undetected in generated feedback. A successful fix reworks the `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` regex lists (or the matching approach) to catch these common phrasing variations — covering verbs like "can't"/"lack"/"struggle" and subject variants like "developers"/"programmers"/"graduates" — while still passing the existing tests that assert neutral/positive mentions of bootcamps or educational background are not flagged.

**Branch name:** fix/151-bias-detector-too-narrow

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [commit link](https://github.com/Harsh-D20/pathreview/commit/a6de94d85f04585a36c050509589de238312f7c4)

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_bias_detector.py -v` and confirmed 9 of 32 tests fail exactly as described in the issue — e.g. `test_dismissive_bootcamp_language_detected` ("bootcamp graduates can't write production code") and `test_demographic_assumption_age_detected` ("young developers can't handle complex systems") both return `is_biased=False` because the existing regexes only match singular subjects and a narrow set of verb phrasings. Documented the root cause with an inline comment in `safety/bias_detector.py`.

**PLAN.md link:** [PLAN.md link](https://github.com/Harsh-D20/pathreview/blob/fix/151-bias-detector-too-narrow/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None currently — candidate regex patterns for both `DISMISSIVE_PATTERNS` and `DEMOGRAPHIC_PATTERNS` were hand-validated against all 32 test assertions in a scratch script (0 mismatches) before writing PLAN.md, so the approach is de-risked going into implementation in Week 9. Still need to apply the patterns to `safety/bias_detector.py` itself and confirm against the real `pytest` run (scratch validation isn't a substitute for that).